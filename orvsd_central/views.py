from flask import (request, render_template, flash, g, session, redirect,
                   url_for, abort, jsonify)
from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from werkzeug import check_password_hash, generate_password_hash
from orvsd_central import db, app, login_manager, google, celery
from forms import LoginForm, AddUser, InstallCourse
from models import (District, School, Site, SiteDetail,
                    Course, CourseDetail, User)
from sqlalchemy import func, and_
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import eagerload
from models import (District, School, Site, SiteDetail,
                    Course, CourseDetail, User)
import constants
import celery
from bs4 import BeautifulSoup as Soup
import os
from celery.utils.encoding import safe_repr, safe_str
import json
import re
import subprocess
import StringIO
import requests
import zipfile
import datetime
import urllib
import itertools


"""
ACCESS
"""


@app.route("/register", methods=['GET', 'POST'])
#@login_required
def register():
    #user=current_user
    form = AddUser()
    message = ""

    if request.method == "POST":
        if form.password.data != form.confirm_pass.data:
            message = "The passwords provided did not match!\n"
        elif not re.match('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$',
                          form.email.data):
            message = "Invalid email address!\n"
        else:
            # Add user to db
            db.session.add(User(name=form.user.data,
                                email=form.email.data,
                                password=form.password.data,
                                role=constants.USER_PERMS
                                              .get(form.perm.data, 1)))
            db.session.commit()
            message = form.user.data+" has been added successfully!\n"

    return render_template('add_user.html', form=form,
                           message=message, user=current_user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(name=form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.")
            return redirect("/report")
        else:
            flash("Username/Password combo was not recognized.  "
                  "Please try again.")
    return render_template("login.html", form=form)


@app.route("/google_login")
def google_login():
    access_token = session.get('access_token')
    if access_token is None:
        callback = url_for('authorized', _external=True)
        return google.authorize(callback=callback)
    else:
        access_token = access_token
        headers = {'Authorization': 'OAuth '+access_token}
        req = urllib2.Request('https://www.googleapis.com/oauth2/v1/userinfo',
                              None, headers)
        try:
            res = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 401:
                session.pop('access_token', None)
                flash('There was a problem with your Google \
                      login information.  Please try again.')
                return redirect(url_for('login'))
            return res.read()
        obj = json.loads(res.read())
        email = obj['email']
        user = User.query.filter_by(email=email).first()
        #pop access token so it isn't sitting around in our
        #session any longer than nescessary
        session.pop('access_token', None)
        if user is not None:
            login_user(user)
            return redirect(url_for('report'))
        else:
            flash("This google account was not recognized \
                  as having access. Sorry.")
            return redirect(url_for('login'))


@app.route(app.config['REDIRECT_URI'])
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token
    return redirect(url_for('google_login'))


@app.route('/me')
@login_required
def home():
    """
    Loads a users home information page
    """
    #not sure current_user works this way, write test
    return render_template('users/templates/profile.html', user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


"""
INSTALL
"""


@app.route('/get_site_by/<int:site_id>', methods=['GET'])
def site_by_id(site_id):
    name = Site.query.filter_by(id=site_id).first().name
    return jsonify(name=name)


@app.route('/install/course', methods=['GET', 'POST'])
def install_course():
    """
    Displays a form for the admin user to pick courses to install on a site

    Returns:
        Rendered template
    """

    if request.method == 'GET':
        form = InstallCourse()

        # Query all moodle 2.2 courses
        courses = db.session.query(CourseDetail).filter(CourseDetail
                                                        .moodle_version
                                                        .like("2.5%")).all()

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

        site_url = Site.query.filter_by(id=request.form.get('site'))\
                             .first().baseurl

        # The site to install the courses
        site = ("http://%s/webservice/rest/server.php?"
                "wstoken=%s&wsfunction=%s") % \
               (site_url,
                app.config['INSTALL_COURSE_WS_TOKEN'],
                app.config['INSTALL_COURSE_WS_FUNCTION'])
        site = str(site.encode('utf-8'))

        # The CourseDetail objects needed to generate the url
        courses = []
        for cid in selected_courses:
            courses.append(CourseDetail.query.filter_by(id=cid)
                           .order_by(CourseDetail.updated.desc())
                           .first())

        site_ids = [site_id for site_id in request.form.getlist('site')]
        site_urls = [Site.query.filter_by(id=site_id).first().baseurl
                     for site_id in site_ids]

        for course in courses:
            for site_url in site_urls:
                # The site to install the courses
                site = ("http://%s/webservice/rest/server.php?"
                        "wstoken=%s&wsfunction=%s") % \
                       (site_url,
                        app.config['INSTALL_COURSE_WS_TOKEN'],
                        app.config['INSTALL_COURSE_WS_FUNCTION'])
                site = str(site.encode('utf-8'))

                # Courses are detached from session for being
                # inactive for too long.
                course.course.name

                install_course_to_site.delay(course, site)

            output += (str(len(site_urls)) + " course install(s) for " +
                       course.course.name + " started.\n")

        return render_template('install_course_output.html',
                               output=output,
                               user=current_user)


@app.route("/courses/filter", methods=["POST"])
def get_course_list():
    dir = request.form.get('filter')

    if dir == "None":
        courses = CourseDetail.query.all()
    else:
        courses = db.session.query(CourseDetail).join(Course) \
                    .filter(Course.source == dir).all()

    # This means the folder selected was not the source folder or None.
    if not courses:
        courses = db.session.query(CourseDetail).filter(CourseDetail.filename
                                                        .like("%"+dir+"%"))\
                                                .all()

    courses = sorted(courses, key=lambda x: x.course.name)

    serialized_courses = [{'id': course.course_id,
                           'name': course.course.name}
                          for course in courses]
    return jsonify(courses=serialized_courses)


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

@login_required
@app.route("/schools/<id>/view")
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
                        drupal_siteinfo=drupal_siteinfo, user=current_user)

    else:
        return "Page not found..."


@app.route('/report/get_schools', methods=['POST'])
def get_schools():
    # From the POST, we need the district id, or distid
    dist_id = request.form.get('distid')

    # Given the distid, we get all the schools
    if dist_id:
        schools = School.query.filter_by(district_id=dist_id) \
                              .order_by("name").all()
    else:
        schools = School.query.order_by("name").all()

    # the dict to be jsonify'd
    school_list = {}

    for school in schools:
        sitedata = []
        sites = Site.query.filter(Site.school_id == school.id).all()
        for site in sites:
            admin = None
            sd = SiteDetail.query.filter(SiteDetail.site_id == site.id)\
                                 .order_by(SiteDetail.timemodified.desc())\
                                 .first()
            if sd:
                admin = sd.adminemail
            sitedata.append({'name': site.name,
                             'baseurl': site.baseurl,
                             'sitetype': site.sitetype,
                             'admin': admin})
        school_list[school.shortname] = {'name': school.name,
                                         'id': school.id,
                                         'sitedata': sitedata}

    # Returned the jsonify'd data of counts and schools for jvascript to parse
    return jsonify(schools=school_list, counts=district_details(schools))


"""
REPORT
"""


@app.route("/report", methods=['GET'])
@login_required
def report():
    all_districts = District.query.order_by("name").all()
    dist_count = len(all_districts)
    school_count = School.query.count()
    site_count = Site.query.count()
    course_count = Course.query.count()

    accord_id = "dist_accord"
    dist_id = "distid=%s"

    data = build_accordion(all_districts, accord_id, "district", dist_id)

    return render_template("report.html",
                           datadump=data,
                           dist_count=dist_count,
                           school_count=school_count,
                           site_count=site_count,
                           course_count=course_count,
                           user=current_user)


@app.route('/')
@login_required
def root():
    if not current_user.is_anonymous():
        return redirect(url_for('report'))
    return redirect(url_for('login'))


"""
UPDATE
"""


@app.route("/<category>/update")
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
REMOVE
"""


@app.route("/display/<category>")
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
def remove_objects(category):
    obj = get_obj_by_category(category)
    remove_ids = request.form.getlist('remove')
    for remove_id in remove_ids:
        # obj.query returns a list, but should only have one element because
        # ids are unique.
        remove = obj.query.filter_by(id=remove_id)[0]
        db.session.delete(remove)

    db.session.commit()

    return redirect('display/'+category)


"""
HELPERS
"""


@login_manager.unauthorized_handler
def unauthorized():
    flash('You are not authorized to view this page, please login.')
    return redirect('/login')


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


@google.tokengetter
def get_access_token():
    return session.get('access_token')


def build_accordion(objects, accordion_id, type, extra=None):
    inner_t = app.jinja_env.get_template('accordion_inner.html')
    outer_t = app.jinja_env.get_template('accordion.html')

    inner = ""

    for obj in objects:
        inner_id = re.sub(r'[^a-zA-Z0-9]', '', obj.shortname)
        inner += inner_t.render(accordion_id=accordion_id,
                                inner_id=inner_id,
                                type=type,
                                link=obj.name,
                                extra=None if not extra else extra % obj.id)

    return outer_t.render(accordion_id=accordion_id,
                          dump=inner)


def get_obj_by_category(category):
    # Checking for case insensitive categories
    categories = {'districts': District, 'schools': School,
                  'sites': Site, 'courses': Course, 'users': User,
                  'coursedetails': CourseDetail, 'sitedetails': SiteDetail}

    return categories.get(category.lower())


def get_obj_identifier(category):
    categories = {'districts': 'name', 'schools': 'name',
                  'sites': 'name', 'courses': 'name', 'users': 'name',
                  'coursedetails': 'filename', 'sitedetails': 'site_id'}

    return categories.get(category.lower())


def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()


def district_details(schools):
    """
    district_details adds up the number of teachers, users, and admins of all
    the district's school's sites.

    Args:
        schools (list): list of schools to total the users, teachers, and
         admins.

    Returns:
        dict. The total admins, teachers, and users of the schools
    """

    admin_count = 0
    teacher_count = 0
    user_count = 0

    for school in schools:
        sites = Site.query.filter_by(school_id=school.id).all()
        for site in sites:
            details = SiteDetail.query.filter_by(site_id=site.id) \
                                      .order_by(SiteDetail
                                                .timemodified
                                                .desc()) \
                                      .first()
            if details:
                admin_count += details.adminusers
                teacher_count += details.teachers
                user_count += details.totalusers

    return {'admins': admin_count,
            'teachers': teacher_count,
            'users': user_count}


#ORVSD Central API


@app.route("/1/sites/<baseurl>")
def get_site_by_url(baseurl):
    site = Site.query.filter_by(baseurl=baseurl).first()
    if site:
        site_details = SiteDetail.query.filter_by(site_id=site.id) \
                                       .order_by(SiteDetail
                                                 .timemodified
                                                 .desc()) \
                                       .first()

        site_info = dict(site.serialize().items() +
                         site_details.serialize().items())

        return jsonify(content=site_info)

    return jsonify(content={'error': 'Site not found'})


@app.route("/1/sites/<baseurl>/moodle")
def get_moodle_sites(baseurl):
    school_id = Site.query.filter_by(baseurl=baseurl).first().school_id
    moodle_sites = Site.query.filter_by(school_id=school_id).all()
    data = [{'id': site.id, 'name': site.name} for site in moodle_sites]
    return jsonify(content=data)


@app.route('/celery/status/<celery_id>')
def get_task_status(celery_id):
    status = db.session.query("status")\
                       .from_statement("SELECT status FROM celery_taskmeta"
                                       " WHERE id=:celery_id")\
                       .params(celery_id=celery_id).first()
    return jsonify(status=status)


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
#        for source in os.listdir(base_path):
        sources = [source+"/" for source in os.listdir(base_path)]
        for source in sources:
            for root, sub_folders, files in os.walk(base_path+source):
                for file in files:
                    full_file_path = os.path.join(root, file)
                    file_path = full_file_path.replace(base_path+source, '')
                    course = CourseDetail.query.filter_by(filename=file_path)\
                                               .first()
                    # Check to see if it exists in the database already

                    if not course and os.path.isfile(full_file_path):
                        create_course_from_moodle_backup(base_path,
                                                         file_path, source)
                        num_courses += 1

        if num_courses > 0:
            flash(str(num_courses) + ' new courses added successfully!')
    return render_template('update_courses.html', user=current_user)


def create_course_from_moodle_backup(base_path, file_path, source):
    # Needed to delete extracted xml once operation is done
    project_folder = "/home/vagrant/orvsd_central/"

    # Unzip the file to get the manifest (All course backups are zip files)
    zip = zipfile.ZipFile(base_path+source+file_path)
    xmlfile = file(zip.extract("moodle_backup.xml"), "r")
    xml = Soup(xmlfile.read(), "xml")
    info = xml.moodle_backup.information
    old_course = Course.query\
                       .filter_by(name=info.original_course_fullname.string)\
                       .first() or Course.query\
                                         .filter_by(shortname=
                                                    info
                                                    .original_course_shortname
                                                    .string).first()

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
