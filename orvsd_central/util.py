"""
Utility class containing useful methods not tied to specific models or views
"""
from bs4 import BeautifulSoup as Soup
import json
import logging
import os
import re
import zipfile
from datetime import datetime
from functools import wraps
from getpass import getpass

from celery import Celery
from flask import current_app, flash, g, redirect, render_template
from flask.ext.login import LoginManager, current_user
from flask.ext.oauth import OAuth
import requests
from requests.exceptions import ConnectionError

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


def create_course_from_moodle_backup(base_path, source, file_path):
    """
    This creates a Course object from a backup xml file for FLVS/NROC courses.

    We do this by extracting the zip file containing the xml, pulling the
    required data from moodle.xml, and then creating our Course object.

    The full file path format looks something like this:
        base_path          |   source  |          file_path
    /data/moodle2_masters      /flvs       /flvs_osl_2012/backup_algebra2.xml
        ^ This path can be modified in your config/default.py file ^

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
    zip = zipfile.ZipFile(base_path + source + file_path)
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


def gather_siteinfo(site, from_when=7):
    """
    Using the siteinfo webservice plugin for moodle, gather the siteinfo data
    about a site
    """

    # Verify we have a site object
    if not hasattr(site, 'moodle_tokens'):
        logging.error("Is this a site?")
        return

    # If we have the siteinfo token, lets grab the data
    siteinfo_token = site.get_token('orvsd_siteinfo')
    if siteinfo_token:
        site_url = ("http://%s" % site.baseurl
                    if not site.baseurl.startswith("http") else site.baseurl)

        # Make the request
        req = requests.post(
            url="%s/webservice/rest/server.php" % site_url,
            data={
                'wstoken': siteinfo_token,
                'wsfunction': 'local_orvsd_siteinfo_siteinfo',
                'moodlewsrestformat': 'json',
                'datetime': str(from_when)
            }
        )

        try:
            # Add this data to the site details table
            gathered_info = req.json()

            # Check for errors from moodle
            if gathered_info.get('error', None):
                logging.error(
                    "%s: %s" % (site.name, gathered_info['error'])
                )
                return
            elif gathered_info.get('exception', None):
                logging.error(
                    "%s: %s" % (site.name, gathered_info['exception'])
                )
                return
        except ValueError:
            # REST may be disabled
            if req.status_code == 403:
                logging.error(
                    "%s: 403 Returned, is the REST service enabled?" %
                    site.name
                )
            # Response given by the site
            logging.error(
                "%s: did not receive json: '%s'" %
                (site.name, req.text)
            )
            return

        # handle the adminlist
        adminlist = json.dumps(gathered_info.get('adminlist', ''))

        site_details = SiteDetail(
            site_id=site.id,
            courses=gathered_info.get('courses', ''),
            siteversion=gathered_info.get('siteversion', ''),
            siterelease=gathered_info.get('siterelease', ''),
            adminlist=adminlist,
            totalusers=gathered_info.get('totalusers', 0),
            adminusers=gathered_info.get('adminusers', 0),
            teachers=gathered_info.get('teachers', 0),
            activeusers=gathered_info.get('activeusers', 0),
            totalcourses=gathered_info.get('totalcourses', 0),
            timemodified=datetime.now()
        )

        g.db_session.add(site_details)
        g.db_session.commit()


def gather_tokens(sites=[], service_names=[]):
    """
    gather_tokens will get tokens required for moodle webservices provided in
    the list of service_names list

    sites: list of moodle sites to get tokens from
    service_names: list of service names to get tokens for
    """

    # If there are no sites listed, why is this even being called?
    if sites == []:
        return

    # We allow for service names to be passed, though most likely only services
    # listed in the applications config will ever be used
    if service_names == []:
        service_names = current_app.config['MOODLE_SERVICES']

    # If no services, whys is the even being called?
    if not service_names:
        return

    # For each site in the list of sites we need to get tokens
    for site in sites:
        # If the object was built odly and no baseurl exists, move onto the
        # next sit
        if site.baseurl in ['', None]:
            continue

        # For the request, prepend the protocol if necessary
        site_url = ("http://%s" % site.baseurl
                    if not site.baseurl.startswith("http") else site.baseurl)

        # For each service, gather a token
        for service in service_names:
            try:
                # Using the siteurl and the account information stored in the
                # config, request a token for the given service
                resp_data = {
                    'username': current_app.config['INSTALL_COURSE_USERNAME'],
                    'password': current_app.config['INSTALL_COURSE_PASS'],
                    'service': service
                }
                resp = requests.post(
                    "%s/login/token.php" % site_url,
                    data=resp_data
                )
            except ConnectionError:
                logging.error("%s: Unable to connect to the site" % site.name)
                continue

            # Try and decode the json, if we did not receive json, we need to
            # return the string (resp.text) back to the user as an error
            try:
                returned = resp.json()
                # Check for an error log and continue
                if 'error' in returned:
                    logging.error("%s:  %s" % (
                        site.name,
                        returned['error']
                    ))
                    continue
                else:
                    current_tokens = site.get_moodle_tokens()
                    # Assign the service the retreived token
                    current_tokens[service] = returned['token']
                    # dump the json string and store it for the site
                    site.moodle_tokens = json.dumps(current_tokens)
                    # Commit the change to the database
                    g.db_session.commit()
                    logging.info(
                        "Added '%s':'%s' to %s" %
                        (service, returned['token'], site_url)
                    )
            except ValueError:
                # Unable to parse JSON, log the problem
                logging.warning(
                    "Unable to parse JSON for %s: %s" %
                    (site_url, resp.text)
                )


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
        ^ This path can be modified in your config/default.py file ^

    Args:
        base_path (string) - The path to our FLVS/NROC folders.
        file_path (string) - Full file path to the file we are extracting.

    Returns:
        A tuple with the source and file path (as listed above).
    """
    path = file_path.replace(base_path, '').partition('/')
    return path[0] + '/', path[2]


def get_active_counts():
    """
    Get the active counts of all the things - schools, sites, districts, users,
    admins, and teachers
    """

    # Dictionary being returned of all count data
    active_counts = {
        'districts': 0,
        'schools': 0,
        'sites': 0,
        'courses': Course.query.count(),
        'admins': 0,
        'teachers': 0,
        'totalusers': 0,
        'activeusers': 0
    }

    # Starting from the perspective of sites
    sites = Site.query.join(SiteDetail).distinct().all()

    # When looking for districts and schools, record unique names and count
    # those at the end
    active_schools = set()
    active_districts = set()

    # For each site, check if there is a SiteDetail associated. If there is,
    # that means the site is active and we want all the details about users.
    for site in sites:
        sd = SiteDetail.query.filter(
            SiteDetail.site_id == site.id
        ).order_by(
            SiteDetail.timemodified.desc()
        ).first()

        if sd:
            # Grab all the details about the users
            active_counts['admins'] += sd.adminusers
            active_counts['teachers'] += sd.teachers
            active_counts['totalusers'] += sd.totalusers
            active_counts['activeusers'] += sd.activeusers
            active_counts['sites'] += 1

            # Add the school and district names to their respective sets for
            # later counting
            school = School.query.filter(School.id == site.school_id).first()
            if school:
                active_schools.add(school.name)
                district = District.query.filter(
                    District.id == school.district_id
                ).first()
                if district:
                    active_districts.add(district.name)

    # Count all the unique schools and districts
    active_counts['districts'] = len(active_districts)
    active_counts['schools'] = len(active_schools)

    return active_counts


def get_schools(dist_id, active):
    """
    Gets the active or inactive schools for a given ditrict.

    An active school is defined by said school not only having a site, but also
    a SiteDetail with at least one admin, teacher, or user

    dist_id -- ID of a district to narrow the school search down with
    active  -- Status of schools to find
    """

    # Get all schools in the district with dist_id
    schools = School.query.filter_by(district_id=dist_id)
    active_schools = schools.join(Site).join(SiteDetail).distinct()

    # Dict to return for the report
    district_info = {}

    for school in active_schools:
        # Get the sites associated with the school
        sites = Site.query.filter_by(school_id=school.id).distinct()

        for site in sites:
            details = SiteDetail.query.filter_by(site_id=site.id).order_by(
                SiteDetail.timemodified.desc()
            ).first()

            district_info[str(site.id)] = {}
            district_info[str(site.id)]['sitename'] = site.name
            district_info[str(site.id)]['schoolname'] = school.name
            district_info[str(site.id)]['schoolid'] = school.id
            district_info[str(site.id)]['baseurl'] = site.baseurl
            if details:
                district_info[str(site.id)]['admin'] = details.adminlist
                district_info[str(site.id)]['teachers'] = details.teachers
                district_info[str(site.id)]['users'] = details.activeusers
                district_info[str(site.id)]['courses'] = (
                    len(json.loads(details.courses)) if details.courses else 0
                )

    return district_info

@celery.task(name='tasks.update_course_list')
def update_courselist_task():
        num_courses = 0
        base_path = current_app.config.get('INSTALL_COURSE_FILE_PATH', None)
        mdl_files = []


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

        details = g.db_session.query(CourseDetail) \
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
            logging.info("Added %s new courses!" % num_courses)


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
            'category': current_app.config['INSTALL_COURSE_CATEGORY'],
            'firstname': current_app.config['INSTALL_COURSE_FIRSTNAME'],
            'lastname': current_app.config['INSTALL_COURSE_LASTNAME'],
            'city': current_app.config['INSTALL_COURSE_CITY'],
            'username': current_app.config['INSTALL_COURSE_USERNAME'],
            'email': current_app.config['INSTALL_COURSE_EMAIL'],
            'pass': current_app.config['INSTALL_COURSE_PASS']}

    resp = requests.post(install_url, data=data, timeout=None)

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


def is_valid_email(email):
    """
    Check that `email` is not empty and looks like an e-mail.
    """
    if not email:
        return False

    if not re.match(
        '^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$',
        email,
    ):
        return False

    return True


def prompt_valid_email():
    """
    Prompts for an email that does not already exist
    in the database.

    Returns: a valid and unique email.
    """
    email = raw_input("E-mail: ")
    while not is_valid_email(email):
        print("E-mail appears to be invalid.")
        email = raw_input("E-mail: ")

    return email


def prompt_matching_passwords():
    """
    Returns valid matching passwords from the prompt.
    """
    matching = False
    while not matching:
        passwd = getpass("Password: ")
        if not passwd:
            print("Please enter a password.")
            continue

        confirm = getpass("Confirm: ")
        matching = passwd == confirm
        if not matching:
            print("Passwords do not match. Please try again.")

    return passwd
