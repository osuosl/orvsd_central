"""
Utility class containing useful methods not tied to specific models or views
"""
from bs4 import BeautifulSoup as Soup
import os
import re
import zipfile
from datetime import datetime
from functools import wraps

from celery import Celery
from flask import current_app, flash, g, jsonify, redirect, render_template
from flask.ext.login import LoginManager, current_user
from flask.ext.oauth import OAuth
from oursql import DictCursor, connect
import requests

from orvsd_central import constants
from orvsd_central.database import create_db_session
from orvsd_central.models import (District, School, Site, SiteDetail,
                                  Course, CourseDetail, User)

# Set up a google oath object for user authentication.
google = OAuth().remote_app(
    'google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    request_token_url=None,
    request_token_params={
        'scope':
        'https://www.googleapis.com/auth/userinfo.email', 'response_type':
        'code'},
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_method='POST',
    access_token_params={'grant_type': 'authorization_code'},
    consumer_key=current_app.config['GOOGLE_CLIENT_ID'],
    consumer_secret=current_app.config['GOOGLE_CLIENT_SECRET'])

# Initialize the login manager for Flask-Login.
login_manager = LoginManager()
login_manager.setup_app(current_app)


def init_celery():
    celery = Celery(current_app.import_name,
                    broker=current_app.config['CELERY_BROKER_URL'])
    celery.conf.update(current_app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with current_app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = init_celery()


@current_app.teardown_appcontext
def shutdown_session(exception=False):
    """
    Destroys the current db_session if it exists.
    """
    if g.get('db_session'):
        g.db_session.remove()


@current_app.before_request
def setup_db_session():
    """
    Creates a db_session if it doesn't exist.
    * This is done before a request is processed.
    """
    if not g.get('db_session'):
        g.db_session = create_db_session()


@current_app.errorhandler(404)
def page_not_found(e):
    """
    Standard page not found handler.
    """
    return render_template('404.html', user=current_user), 404


def build_accordion(districts, active_accordion_id, inactive_accordion_id,
                    type, user, extra=None):
    """
    Builds the accordion from pre-defined templates.
    * Note: There is some complex logic in here to differentiate schools
            with and without students/teachers/admins. These usually refer
            back to the database entries that we have on districts/schools, but
            are not continuously tracking.
    """
    inner_t = current_app.jinja_env.get_template('accordion_inner.html')
    outer_t = current_app.jinja_env.get_template('accordion.html')

    active_inner = ""
    inactive_inner = ""

    # Find all active schools (a school with a site that has a SiteDetail)
    active_schools = set(
        g.db_session.query(School).join(Site).join(SiteDetail).distinct().all()
    )

    # All other schools are inactive
    inactive_schools = set(g.db_session.query(School).all()) - active_schools

    # Get the district ids of active and inactive schools
    active_district_ids = set(
        int(school.district_id) for school in active_schools
    )
    inactive_district_ids = set(
        int(school.district_id) for school in inactive_schools
    )

    # List of districts in the
    active_districts = set(
        district for district in districts
        if district.id in active_district_ids
    )
    inactive_districts = set(
        district for district in districts
        if district.id in inactive_district_ids
    )

    for district in sorted(active_districts, key=lambda x: x.shortname):
        inner_id = "%s_active" % district.shortname
        active_inner += inner_t.render(
            accordion_id=active_accordion_id,
            inner_id=inner_id,
            type=type,
            link=district.name,
            extra=None if not extra else extra % district.id
        )

    for district in sorted(inactive_districts, key=lambda x: x.shortname):
        inner_id = "%s_inactive" % district.shortname
        inactive_inner += inner_t.render(
            accordion_id=active_accordion_id,
            inner_id=inner_id,
            type=type,
            link=district.name,
            extra=None if not extra else extra % district.id
        )

    return outer_t.render(active_accordion_id=active_accordion_id,
                          inactive_accordion_id=inactive_accordion_id,
                          active=active_inner,
                          active_count=len(active_districts),
                          inactive=inactive_inner,
                          inactive_count=len(inactive_districts),
                          user=user)


def create_course_from_moodle_backup(base_path, source, file_path):
    """
    This creates a Course object from a backup xml file for FLVS/NROC courses.

    We do this by extracting the zip file containing the xml, pulling the
    required data from moodle.xml, and then creating our Course object.

    The full file path format looks something like this:
        base_path          |   source  |          file_path
    /data/moodle2_masters      /flvs       /flvs_osl_2012/backup_algebra2.xml

    Args:
        base_path (string) - The path to our FLVS/NROC folders.
        source (string) - FLVS/NROC/other course types.
        file_path (string) - File path to the file we are extracting.
                    * This may have folders in the file name, for example:
                    "flvs_osl_2912/backup_algebra2.xml" is a valid file_path.

    Returns:
        Nothing
    """
    # Needed to delete extracted xml once operation is done
    project_folder = current_app.config["PROJECT_PATH"]

    # Unzip the file to get the manifest (All course backups are zip files)
    zip = zipfile.ZipFile(base_path+source+file_path)
    xmlfile = file(zip.extract("moodle_backup.xml"), "r")
    xml = Soup(xmlfile.read(), "lxml")
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
        g.db_session.add(new_course)

        # Until the session is committed, the new_course does not yet have
        # an id.
        g.db_session.commit()

        course_id = new_course.id
    else:
        course_id = old_course.id

    _version_re = re.findall(r'_v(\d)_', file_path)

    # Regex will only be a list if it has a value in it
    version = _version_re[0] if list(_version_re) else None

    new_course_detail = CourseDetail(course_id=course_id,
                                     filename=file_path,
                                     version=version,
                                     updated=datetime.now(),
                                     active=True,
                                     moodle_version=info.moodle_release.string,
                                     moodle_course_id=info
                                                     .original_course_id
                                                     .string)

    g.db_session.add(new_course_detail)
    g.db_session.commit()

    # Get rid of moodle_backup.xml
    os.remove(os.path.join(project_folder, "moodle_backup.xml"))


def district_details(schools, active):
    """
    district_details adds up the number of teachers, users, and admins of all
    the district's school's sites.

    Args:
        schools (list): list of schools to total the users, teachers, and
         admins.
        active: Are we calculating for an active or inactive district?

    Returns:
        dict. The total admins, teachers, and users of the schools
    """

    admin_count = 0
    teacher_count = 0
    user_count = 0

    # Only look at counts if the schools are in the 'active' category.
    if active:
        for school in schools:
            sites = Site.query.filter_by(school_id=school.id).all()
            for site in sites:
                details = SiteDetail.query.filter_by(site_id=site.id) \
                                          .order_by(SiteDetail
                                                    .timemodified
                                                    .desc()) \
                                          .first()
                if details:
                    admin_count += details.adminusers or 0
                    teacher_count += details.teachers or 0
                    user_count += details.totalusers or 0

    return {'admins': admin_count,
            'teachers': teacher_count,
            'users': user_count}


def gather_siteinfo():
    """
    Gathers moodle/drupal site information to be put into our db.
    * This is where all of our SiteDetail objects are generated.
    """
    user = current_app.config['SITEINFO_DATABASE_USER']
    password = current_app.config['SITEINFO_DATABASE_PASS']
    address = current_app.config['SITEINFO_DATABASE_HOST']

    # Connect to gather the db list
    con = connect(host=address, user=user, passwd=password)
    curs = con.cursor()

    # find all the databases with a siteinfo table
    find = ("SELECT table_schema, table_name "
            "FROM information_schema.tables "
            "WHERE table_name =  'siteinfo' "
            "OR table_name = 'mdl_siteinfo';")

    curs.execute(find)
    check = curs.fetchall()
    con.close()

    # store the db names and table name in an array to sift through
    db_sites = []
    if len(check):
        for pair in check:
            db_sites.append(pair)

    unknown_district = District.query.filter_by(
        name='z No district found'
    ).first()

    # for each relevent database, pull the siteinfo data
    for database in db_sites:
        cherry = connect(
            user=user,
            passwd=password,
            host=address,
            db=database[0]
        )

        # use DictCursor here to get column names as well
        pie = cherry.cursor(DictCursor)

        # Grab the site info data
        pie.execute("select * from `%s`;" % database[1])
        data = pie.fetchall()
        cherry.close()

        # For all the data, shove it into the central db
        for d in data:
            # what version of moodle is this from?
            # version = d['siterelease'][:3]

            # what is our school domain? take the protocol
            # off the baseurl
            school_re = 'http[s]{0,1}:\/\/'
            school_url = re.sub(school_re, '', d['baseurl'])

            # try to figure out what machine this site lives on
            if 'location' in d:
                if d['location'][:3] == 'php':
                    location = 'platform'
                else:
                    location = 'unknown'

                # get the school
                school = School.query.filter_by(domain=school_url).first()

                # If no match is found by domain, try looking up by name
                if not school:
                    school = School.query.filter_by(name=d['sitename']).first()

                # if no school exists, create a new one with
                # name = sitename, district_id = 0 (special 'Unknown'
                # district)
                if school is None:
                    school = School(
                        name=d['sitename'],
                        shortname=d['sitename'],
                        domain=school_url,
                        license='',
                        state_id=None
                    )

                    dist_id = unknown_district.id
                    if school_url:
                        # Lets try the full school_url first.
                        similar_schools = g.db_session.query(School).filter(
                            School.domain.like("%" + school_url + "%")
                        ).all()

                        if not similar_schools:
                            # Fine, let's cut off the first subdomain.
                            broad_url = school_url[school_url.find('.'):]
                            similar_schools = g.db_session.query(School) \
                                .filter(School.domain.like(
                                    "%" + broad_url + "%"
                                )).all()

                        if similar_schools:
                            dist_id = similar_schools[0].district_id
                            for school in similar_schools:
                                if school.district_id != dist_id:
                                    # If all results don't match, they
                                    # aren't accurate enough.
                                    dist_id = unknown_district.id
                                    break

                    school.district_id = dist_id
                    g.db_session.add(school)
                    g.db_session.commit()

                # find the site
                site = Site.query.filter_by(baseurl=school_url).first()

                # if no site exists, make a new one, school_id = school.id
                if site is None:
                    site = Site(
                        name=d['sitename'],
                        sitetype=d['sitetype'],
                        baseurl='',
                        basepath='',
                        jenkins_cron_job=None,
                        location='',
                        school_id=None
                    )

                site.school_id = school.id

                site.baseurl = school_url
                site.basepath = d['basepath']
                site.location = location
                g.db_session.add(site)
                g.db_session.commit()

                # create new site_details table
                # site_id = site.id, timemodified = now()
                now = datetime.now()
                site_details = SiteDetail(
                    siteversion=d['siteversion'],
                    siterelease=d['siterelease'],
                    adminemail=d['adminemail'],
                    totalusers=d['totalusers'],
                    adminusers=d['adminusers'],
                    teachers=d['teachers'],
                    activeusers=d['activeusers'],
                    totalcourses=d['totalcourses'],
                    timemodified=now
                )
                site_details.site_id = site.id

                # if there are courses on this site, try to
                # associate them with our catalog
                if d['courses']:
                    # quick and ugly check to make sure we have
                    # a json string
                    if d['courses'][:2] != '[{':
                        continue

                    """
                    @TODO: create the correct association
                           model for this to work

                    courses = json.loads(d['courses'])
                    associated_courses = []

                    for i, course in enumerate(courses):
                        if course['serial'] != '0':
                            course_serial = course['serial'][:4]
                            orvsd_course = Course.query
                                                 .filter_by(serial=
                                                            course_serial)
                                                 .first()
                            if orvsd_course:
                                # store this association
                                # delete this course from the json string
                                pass

                    # put all the unknown courses back in the
                    # site_details record
                    site_details.courses = json.dumps(courses)
                    """

                    site_details.courses = d['courses']

                g.db_session.add(site_details)
                g.db_session.commit()


def get_course_folders(base_path):
    """
    Retrieves all folders in a given directory and their subdirectories.
        * This only traverses 1 level deep.

    This is meant to get a list of folders for us to look through for
    filtering courses on the 'Course Install' page.

    Args:
        base_path (string): Path to the top level directory to look through

    Returns:
        All folders in a given directory and their subdirectories.
    """
    folders = ['None']
    for root, sub_folders, files in os.walk(base_path):
        for folder in sub_folders:
            if folder not in folders:
                folders.append(folder)
    return folders


def get_obj_by_category(category):
    """
    Maps categories to model objects.
    """
    # Checking for case insensitive categories
    categories = {'districts': District, 'schools': School,
                  'sites': Site, 'courses': Course, 'users': User,
                  'coursedetails': CourseDetail, 'sitedetails': SiteDetail}

    return categories.get(category.lower())


def get_obj_identifier(category):
    """
    Maps categories to their identifier.
    An identifier is which piece of information we show to users
    to help them identify a specific object.
    """
    categories = {'districts': 'name', 'schools': 'name',
                  'sites': 'name', 'courses': 'name', 'users': 'name',
                  'coursedetails': 'filename', 'sitedetails': 'site_id'}

    return categories.get(category.lower())


# /base_path/source/path is the format of the parsed directories.
def get_path_and_source(base_path, file_path):
    """
    Takes a base_path and full_file_path and returns the source and file_path.

    The full file path format looks something like this:
        base_path          |   source  |          file_path
    /data/moodle2_masters      /flvs       /flvs_osl_2012/backup_algebra2.xml

    Args:
        base_path (string) - The path to our FLVS/NROC folders.
        file_path (string) - Full file path to the file we are extracting.

    Returns:
        A tuple with the source and file path (as listed above).
    """
    path = file_path.replace(base_path, '').partition('/')
    return path[0] + '/', path[2]


def get_schools(dist_id, active):
    """
    Gets the active or inactive schools for a given ditrict.

    An active school is defined by said school not only having a site, but also
    a SiteDetail with at least one admin, teacher, or user

    dist_id -- ID of a district to narrow the school search down with
    active  -- Status of schools to find
    """

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
        admincount = 0
        teachercount = 0
        usercount = 0

        sites = Site.query.filter(Site.school_id == school.id).all()
        for site in sites:
            admin = None
            sd = SiteDetail.query.filter(SiteDetail.site_id == site.id)\
                                 .order_by(SiteDetail.timemodified.desc())\
                                 .first()
            if sd:
                admin = sd.adminemail
                admincount += sd.adminusers or 0
                teachercount += sd.teachers or 0
                usercount += sd.totalusers or 0

            sitedata.append({'name': site.name,
                             'baseurl': site.baseurl,
                             'sitetype': site.sitetype,
                             'admin': admin})

        # Get around potential moodle plugin issues
        totalcount = admincount + teachercount + usercount

        usercount = usercount - admincount - teachercount
        # For active schools, the totalcount better be greater than 0
        if active and totalcount > 0:
            school_list[school.shortname] = {'name': school.name,
                                             'id': school.id,
                                             'admincount': admincount,
                                             'teachercount': teachercount,
                                             'usercount': usercount,
                                             'sitedata': sitedata}
        # For inactive, the totalcount better be 0
        elif not active and totalcount == 0:
            school_list[school.shortname] = {'name': school.name,
                                             'id': school.id,
                                             'admincount': admincount,
                                             'teachercount': teachercount,
                                             'usercount': usercount,
                                             'sitedata': sitedata}

    # Returned the jsonify'd data of counts and schools for jvascript to parse
    return jsonify(schools=school_list,
                   counts=district_details(schools, active))


@celery.task(name='tasks.install_course')
def install_course_to_site(course_detail_id, install_url):
    """
    Installs 'course' to 'site'.
    """
    # To get the file path we need the text input, the lowercase of
    # source, and the filename
    course_detail = CourseDetail.query.filter_by(id=course_detail_id).first()
    course = course_detail.course

    fp = os.path.join(current_app.config['INSTALL_COURSE_FILE_PATH'],
                      course.source)

    data = {'filepath': fp,
            'file': course_detail.filename,
            'courseid': course.id,
            'coursename': course.name,
            'shortname': course.shortname,
            'category': '1',
            'firstname': 'orvsd',
            'lastname': 'central',
            'city': 'none',
            'username': 'admin',
            'email': 'a@a.aa',
            'pass': 'adminpass'}

    resp = requests.post(install_url, data=data)

    return "%s\n\n%s\n\n\n" % (course.shortname, resp.text)


@login_manager.user_loader
def load_user(userid):
    """
    Loads a user via a user_id.
    * This is needed for Flask-Login.
    """
    return User.query.filter_by(id=userid).first()


def string_to_type(string):
    """
    Conversion of javascript strings from forms to correct types for python.
    """
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


def requires_role(role):
    """
    Decorator for defining access to certain actions.

    Levels (as defined in constants.py):
        1 - General User (Implicit with login_required)
        2 - Help Desk
        3 - Admin
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not current_user.is_anonymous():
                if current_user.role >= constants.USER_PERMS.get(role):
                    return f(*args, **kwargs)
                flash("You do not have permission to access this page.")
                return redirect("/")
            # Must check for a logged in user before checking it's attrs.
            return f(*args, **kwargs)
        return wraps(f)(wrapper)
    return decorator
