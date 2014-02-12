import StringIO
import datetime
import json
import os
import re
import subprocess
import requests
from requests.exceptions import HTTPError
import zipfile

from bs4 import BeautifulSoup as Soup
import celery
from celery.utils.encoding import safe_repr, safe_str
from flask import (request, render_template, flash, g, session, redirect,
                   url_for, abort, jsonify)
from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from sqlalchemy import func, and_
from sqlalchemy.orm import eagerload
from sqlalchemy.sql.expression import desc
from werkzeug import check_password_hash, generate_password_hash

from orvsd_central import app, celery, constants, db, google, login_manager
from orvsd_central.forms import LoginForm, AddUser, InstallCourse
from orvsd_central.models import (District, School, Site, SiteDetail,
                                  Course, CourseDetail, User)
from orvsd_central.util import (get_obj_by_category, get_obj_identifier,
                                requires_role)


"""
INSTALL
"""


@app.route('/install/course', methods=['GET', 'POST'])
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
                app.config['INSTALL_COURSE_WS_TOKEN'],
                app.config['INSTALL_COURSE_WS_FUNCTION'])
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



def get_course_folders():
    base_path = "/data/moodle2-masters/"
    folders = ['None']
    for root, sub_folders, files in os.walk(base_path):
        for folder in sub_folders:
            if folder not in folders:
                folders.append(folder)
    return folders


@celery.task(name='tasks.install_course')
def install_course_to_site(course, site):
    # To get the file path we need the text input, the lowercase of
    # source, and the filename
    fp = app.config['INSTALL_COURSE_FILE_PATH']
    fp += 'flvs/'

    data = {'filepath': fp,
            'file': course.filename,
            'courseid': course.course_id,
            'coursename': course.course.name,
            'shortname': course.course.shortname,
            'category': '1',
            'firstname': 'orvsd',
            'lastname': 'central',
            'city': 'none',
            'username': 'admin',
            'email': 'a@a.aa',
            'pass': 'adminpass'}

    resp = requests.post(site, data=data)

    return "%s\n\n%s\n\n\n" % (course.course.shortname, resp.text)


"""
VIEW
"""


@app.route("/schools/<id>/view")
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


"""
UPDATE
"""


@app.route("/<category>/update")
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


@app.route("/<category>/object/add", methods=["POST"])
def add_object(category):
    obj = get_obj_by_category(category)
    if obj:
        inputs = {}
        # Here we update our dict with new values
        # A one liner is too messy :(
        for column in obj.__table__.columns:
            if column.name is not 'id':
                inputs.update({column.name: string_to_type(
                               request.form.get(column.name))})

        new_obj = obj(**inputs)
        db.session.add(new_obj)
        db.session.commit()
        return jsonify({'id': new_obj.id,
                        'message': "Object added successfully!"})

    abort(404)


@app.route("/<category>/<id>", methods=["GET"])
def get_object(category, id):
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=id).first()
        if modified_obj:
            return jsonify(modified_obj.serialize())

    abort(404)


@app.route("/<category>/<id>/update", methods=["POST"])
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


@app.route("/<category>/<id>/delete", methods=["POST"])
def delete_object(category, id):
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=request.form.get("id")).first()
        if modified_obj:
            db.session.delete(modified_obj)
            db.session.commit()
            return "Object deleted successful!"

    abort(404)


@app.route("/<category>/keys")
def get_keys(category):
    obj = get_obj_by_category(category)
    if obj:
        cols = dict((column.name, '') for column in
                    obj.__table__.columns)
        return jsonify(cols)


def string_to_type(string):
    # Have to watch out for the format of true/false/null
    # with javascript strings.
    if string == "true":
        return True
    elif string == "false":
        return False
    elif string == "null":
        return None
    try:
        return float(string)
    except ValueError:
        if string.isdigit():
            return int(string)
    return string


"""
MIGRATE
"""


@app.route("/schools/migrate")
def migrate_schools():
    districts = District.query.all()
    # Unknown district is id = 0
    schools = School.query.filter_by(district_id=0).all()

    return render_template("migrate.html", districts=districts,
                           schools=schools, user=current_user)

"""
REMOVE
"""


@app.route("/display/<category>")
@login_required
def remove(category):
    user = get_user()
    obj = get_obj_by_category(category)
    if obj:
        objects = obj.query.all()
        if objects:
            # fancy way to get the properties of an object
            properties = objects[0].get_properties()
            return render_template('removal.html', category=category,
                                   objects=objects, properties=properties,
                                   user=user)

    abort(404)


@app.route("/remove/<category>", methods=['POST'])
@login_required
def remove_objects(category):
    obj = get_obj_by_category(category)
    remove_ids = request.form.getlist('remove')
    for remove_id in remove_ids:
        # obj.query returns a list, but should only have one element because
        # ids are unique.
        remove = obj.query.filter_by(id=remove_id)[0]
        db.session.delete(remove)

    db.session.commit()

    return redirect('display/' + category)


"""
HELPERS
"""



def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()


#ORVSD Central API



# Get all task IDs
# TODO: Needs testing
@app.route('/celery/id/all')
def get_all_ids():
    # TODO: "result" is another column, but SQLAlchemy
    # complains of some encoding error.
    statuses = db.session.query("id", "task_id", "status",
                                "date_done", "traceback")\
                         .from_statement("SELECT * FROM celery_taskmeta")\
                         .all()

    return jsonify(status=statuses)


@app.route("/courses/update", methods=['GET', 'POST'])
@requires_role('helpdesk')
@login_required
def update_courselist():
    """
        Updates the database to contain the most recent course
        and course detail entries, based on available files.
    """
    num_courses = 0
    base_path = "/data/moodle2-masters/"
    mdl_files = []
    if request.method == "POST":
        # Get a list of all moodle course files
        # for source in os.listdir(base_path):
        for root, sub_folders, files in os.walk(base_path):
            for file in files:
                full_file_path = os.path.join(root, file)
                if os.path.isfile(full_file_path):
                    mdl_files.append(full_file_path)

        filenames = []
        sources = []
        for filename in mdl_files:
            source, path = get_path_and_source(base_path, filename)
            sources.append(source)
            filenames.append(path)

        details = db.session.query(CourseDetail) \
            .join(CourseDetail.course) \
            .filter(CourseDetail.filename.in_(
                    filenames)).all()

        for detail in details:
            if detail.filename in filenames:
                sources.pop(filenames.index(detail.filename))
                filenames.pop(filenames.index(detail.filename))

        for source, file_path in zip(sources, filenames):
            create_course_from_moodle_backup(base_path, source, file_path)
            num_courses += 1

        if num_courses > 0:
            flash(str(num_courses) + ' new courses added successfully!')
    return render_template('update_courses.html', user=current_user)


# /base_path/source/path is the format of the parsed directories.
def get_path_and_source(base_path, file_path):
    path = file_path.strip(base_path).partition('/')
    return path[0]+'/', path[2]


def create_course_from_moodle_backup(base_path, source, file_path):
    # Needed to delete extracted xml once operation is done
    project_folder = "/home/vagrant/orvsd_central/"

    # Unzip the file to get the manifest (All course backups are zip files)
    zip = zipfile.ZipFile(base_path+source+file_path)
    xmlfile = file(zip.extract("moodle_backup.xml"), "r")
    xml = Soup(xmlfile.read(), "xml")
    info = xml.moodle_backup.information

    old_course = Course.query.filter_by(
        name=info.original_course_fullname.string) or \
        Course.query.filter_by(
            name=info.original_course_shortname.string)

    if old_course is not None:
        # Create a course since one is unable to be found with that name.
        new_course = Course(serial=1000 + len(Course.query.all()),
                            source=source.replace('/', ''),
                            name=info.original_course_fullname.string,
                            shortname=info.original_course_shortname.string)
        db.session.add(new_course)

        # Until the session is committed, the new_course does not yet have
        # an id.
        db.session.commit()

        course_id = new_course.id
    else:
        course_id = old_course.id

    _version_re = re.findall(r'_v(\d)_', file_path)

    # Regex will only be a list if it has a value in it
    version = _version_re[0] if list(_version_re) else None

    new_course_detail = CourseDetail(course_id=course_id,
                                     filename=file_path,
                                     version=version,
                                     updated=datetime.datetime.now(),
                                     active=True,
                                     moodle_version=info.moodle_release.string,
                                     moodle_course_id=info
                                                     .original_course_id
                                                     .string)

    db.session.add(new_course_detail)
    db.session.commit()

    #Get rid of moodle_backup.xml
    os.remove(project_folder+"moodle_backup.xml")


@app.route("/1/site/<site_id>/courses")
def get_courses_by_site(site_id):
    #SiteDetails hold the course information we are looking for
    site_details = SiteDetail.query.filter_by(site_id=site_id) \
                                   .order_by(SiteDetail
                                             .timemodified
                                             .desc()) \
                                   .first()

    if site_details and site_details.courses:
        return jsonify(content=json.loads(site_details.courses))
    elif not site_details:
        return jsonify({'error:': 'Site not found.'})
    else:
        return jsonify({'error:': 'No courses found.'})
