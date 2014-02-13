import json

from flask import Blueprint, current_app, render_template, request
from flask.ext.login import current_user, login_required

from orvsd_central import db
from orvsd_central.forms import InstallCourse
from orvsd_central.models import CourseDetail, School, Site, SiteDetail
from orvsd_central.util import (get_course_folders, get_obj_by_category,
                                get_obj_identifier, requires_role)

mod = Blueprint('category', __name__)


"""
All
"""


@mod.route("/<category>/update")
@requires_role('helpdesk')
@login_required
def update(category):
    obj = get_obj_by_category(category)
    identifier = get_obj_identifier(category)
    if obj:
        if 'details' in category:
            category = category.split("details")[0] + " Details"
        category = category[0].upper() + category[1:]

        objects = obj.query.order_by(identifier).all()
        if objects:
            return render_template("update.html", objects=objects,
                                   identifier=identifier, category=category,
                                   user=current_user)

    abort(404)


@mod.route("/<category>/<id>/update", methods=["POST"])
def update_object(category, id):
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=request.form.get("id")).first()
        if modified_obj:
            inputs = {}
            # Here we update our dict with new
            [inputs.update({key: string_to_type(request.form.get(key))})
             for key in modified_obj.serialize().keys()]

            db.session.query(obj).filter_by(id=request.form.get("id"))\
                                 .update(inputs)
            db.session.commit()

            return "Object updated sucessfully!"

    abort(404)


"""
Course
"""


@mod.route('/course/install', methods=['GET', 'POST'])
@requires_role('helpdesk')
@login_required
def install_course():
    """
    Displays a form for the admin user to pick courses to install on a site

    Returns:
        Rendered template
    """

    if request.method == 'GET':
        form = InstallCourse()

        # Query all moodle 2.2 courses
        courses = db.session.query(CourseDetail).filter(
            CourseDetail.moodle_version
            .like('2.5%')
            ).all()

        # Query all moodle sites
        sites = db.session.query(Site).filter(
            Site.sitetype == 'moodle')
        site_details = db.session.query(SiteDetail).filter(
            SiteDetail.siterelease.like('2.2%'))

        moodle_22_sites = []

        # For all sites query the SiteDetail to see if it's a moodle 2.2 site
        for site in sites:
            details = db.session.query(SiteDetail) \
                                .filter(and_(SiteDetail.site_id == site.id,
                                             SiteDetail.siterelease
                                                       .like('2.2%'))) \
                                .order_by(SiteDetail.timemodified.desc()
                                          ).first()

            if details is not None:
                moodle_22_sites.append(site)

        # Generate the list of choices for the template
        courses_info = []
        sites_info = []

        listed_courses = []
        # Create the courses list
        for course in courses:
            if course.course_id not in listed_courses:
                if course.version:
                    courses_info.append(
                        (course.course_id, "%s - v%s" %
                         (course.course.name, course.version)))
                else:
                    courses_info.append(
                        (course.course_id, "%s" %
                         (course.course.name)))
                listed_courses.append(course.course_id)

        # Create the sites list
        for site in moodle_22_sites:
            sites_info.append((site.id, site.baseurl))

        form.course.choices = sorted(courses_info, key=lambda x: x[1])
        form.site.choices = sorted(sites_info, key=lambda x: x[1])
        form.filter.choices = [(folder, folder)
                               for folder
                               in get_course_folders()]

        return render_template('install_course.html',
                               form=form, user=current_user)

    elif request.method == 'POST':
        # Course installation results
        output = ''

        # An array of unicode strings will be passed, they need to be integers
        # for the query
        selected_courses = [int(cid) for cid in request.form.getlist('course')]
        site_ids = [site_id for site_id in request.form.getlist('site')]
        site_urls = [Site.query.filter_by(id=site_id).first().baseurl
                     for site_id in site_ids]

        for site_url in site_urls:
            # The site to install the courses
            site = ("http://%s/webservice/rest/server.php?" +
                    "wstoken=%s&wsfunction=%s") % (
                site_url,
                current_app.config['INSTALL_COURSE_WS_TOKEN'],
                current_app.config['INSTALL_COURSE_WS_FUNCTION'])
            site = str(site.encode('utf-8'))

            # Loop through the courses, generate the command to be run, run it,
            # and append the ouput to output
            #
            # Currently this will break as our db is not setup correctly yet
            for course in courses:
                # Courses are detached from session if inactive for too long.
                course.course.name

                install_course_to_site.delay(course, site)

            output += (str(len(courses)) + " course install(s) for " +
                       site_url + " started.\n")

        return render_template('install_course_output.html',
                               output=output,
                               user=current_user)


"""
School
"""


@mod.route("/schools/<id>/view")
@requires_role('helpdesk')
@login_required
def view_schools(id):
    min_users = 1  # This should be an editable field on the template
                   # that modifies which courses are shown via js.

    school = School.query.filter_by(id=id).first()
    # School license usually defaults to ''.
    school.license = school.license or None

    # Keep them separated for organizational/display purposes
    moodle_sites = db.session.query(Site).filter(and_(
        Site.school_id == id,
        Site.sitetype == 'moodle')).all()

    drupal_sites = db.session.query(Site).filter(and_(
        Site.school_id == id,
        Site.sitetype == 'drupal')).all()

    if moodle_sites or drupal_sites:
        moodle_sitedetails = []
        if moodle_sites:
            for site in moodle_sites:
                site_detail = SiteDetail.query.filter_by(site_id=site.id) \
                    .order_by(SiteDetail
                              .timemodified
                              .desc()) \
                    .first()

        if site_detail and site_detail.courses:
                # adminemail usually defaults to '', rather than None.
                site_detail.adminemail = site_detail.adminemail or None
                # Filter courses to display based on num of users.
                site_detail.courses = filter(
                    lambda x: x['enrolled'] > min_users,
                    json.loads(site_detail.courses)
                )

                moodle_sitedetails.append(site_detail)

        moodle_siteinfo = zip(moodle_sites, moodle_sitedetails)

        drupal_sitedetails = []
        if drupal_sites:
            for site in drupal_sites:
                site_detail = SiteDetail.query.filter_by(site_id=site.id) \
                    .order_by(SiteDetail
                              .timemodified
                              .desc()) \
                    .first()

                if site_detail:
                    site_detail.adminemail = site_detail.adminemail or None

                    drupal_sitedetails.append(site_detail)

        drupal_siteinfo = zip(drupal_sites, drupal_sitedetails)

        return render_template("school.html", school=school,
                               moodle_siteinfo=moodle_siteinfo,
                               drupal_siteinfo=drupal_siteinfo,
                               user=current_user)
    else:
        return render_template("school_data_notfound.html", school=school,
                               user=current_user)
