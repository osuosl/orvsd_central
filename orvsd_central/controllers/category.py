from flask import Blueprint, current_app, render_template, request
from flask.ext.login import current_user, login_required

from orvsd_central import db
from orvsd_central.forms import InstallCourse
from orvsd_central.models import CourseDetail, Site, SiteDetail
from orvsd_central.util import get_course_folders, requires_role

mod = Blueprint('category', __name__)


"""
Course
"""


@mod.route('/install/course', methods=['GET', 'POST'])
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
