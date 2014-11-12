"""
Utility class containing useful methods not tied to specific models or views
"""
from bs4 import BeautifulSoup as Soup
import json
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
from sqlalchemy import create_engine
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

def gather_siteinfo():
    """
    Gathers moodle/drupal site information to be put into our db.
    * This is where all of our SiteDetail objects are generated.
    """

    siteinfo_user = current_app.config['SITEINFO_DATABASE_USER']
    siteinfo_password = current_app.config['SITEINFO_DATABASE_PASS']
    siteinfo_host = current_app.config['SITEINFO_DATABASE_HOST']

    # Site Info DB connection
    siteinfo_engine = create_engine(
        "mysql://%s:%s@%s" % (
            siteinfo_user,
            siteinfo_password,
            siteinfo_host
        )
    )

    # Fancy query to get all moodle sites with the siteinfo plugin
    siteinfo_installed_query = (
        "SELECT table_schema, table_name "
        "FROM information_schema.tables "
        "WHERE table_name =  'siteinfo' "
        "OR table_name = 'mdl_siteinfo';"
    )

    # Query the DB for moodle db's with the plugin installed
    siteinfo_installed = siteinfo_engine.execute(siteinfo_installed_query)

    unknown_district = District.query.filter_by(
        name='z No district found'
    ).first()

    # For each relevant database, get the siteinfo
    for installed in siteinfo_installed:
        '''
        installed[0] - database name
        installed[1] - siteinfo table name
        '''

        # Create a connection to this relevant database
        site_engine = create_engine(
            "mysql://%s:%s@%s/%s" % (
                siteinfo_user,
                siteinfo_password,
                siteinfo_host,
                installed[0]
            )
        )


        # Grab the siteinfo data
        siteinfo_data = site_engine.execute(
            "select * from `%s`" % installed[1]
        )

        # pattern used to remove the baseurl's protocol
        school_re = "https?:\/\/"

        # For all the data, shove it into the central db
        for data in siteinfo_data:
            # Remove the protocol from the base url
            school_url = re.sub(school_re, '', data['baseurl'])

            if 'location' in data and data['location'][:3] == 'php':
                location = 'platform'
            else:
                location = 'unknown'

            # Get the school associated with the school_url
            school = School.query.filter_by(domain=school_url).first()

            # if no school is found by school_url, try by sitename
            if not school:
                school = School.query.filter_by(name=data['sitename']).first()

            # If no school has been found yet, create a new one with
            # a name of sitename in the unknown district
            if not school:
                school = School(
                    name=data['sitename'],
                    shortname=data['sitename'],
                    domain=school_url,
                    license='',
                    state_id=None
                )

                dist_id = unknown_district.id
                if school_url:
                    # Find similar schools
                    similar_schools = g.db_session.query(School).filter(
                        School.domain.like("%%%s%%" % school_url)
                    ).all()

                    if not similar_schools:
                        # No luck still? Let's try without a subdomain
                        broad_url = school_url[school_url.find('.'):]
                        similar_schools = g.db_session.query(School).filter(
                            School.domain.like("%%%s%%" % school_url)
                        ).all()

                    # If we've found similar schools, we'll add this school
                    # to the same domain
                    if similar_schools:
                        dist_id = similar_school[0].district_id

                        # If all results don't match, this isn't
                        # accurate enough
                        for school in similar_schools:
                            if school.district_id != dist_id:
                                dist_id = unknown_district.id
                                break


                # Create the school
                school.district_id = dist_id
                g.db_session.add(school)
                g.db_session.commit()

                # Find the site
                site = Site.query.filter_by(baseurl=school_url).first()

                # if no site exists, make a new one and commit it to the db
                if not site:
                    site = Site(
                        name=data['sitename'],
                        sitetype=data['sitetype'],
                        baseurl=school_url,
                        basepath=data['basepath'],
                        jenkins_cron_job=None,
                        location=location,
                        school_id=school.id
                    )
                g.db_session.add(site)
                g.db_session.commit()

                # Now for the site details
                now = datetime.now()
                site_details = SiteDetail(
                    site_id=site.id,
                    siteversion=data['siteversion'],
                    siterelease=data['siterelease'],
                    adminemail=data['adminemail'],
                    totalusers=data['totalusers'],
                    adminusers=data['adminusers'],
                    teachers=data['teachers'],
                    activeusers=data['activeusers'],
                    totalcourses=data['totalcourses'],
                    timemodified=now
                )

                # if there are courses on this site, try to
                # associate them with our catalog
                if data['courses']:
                    # quick and ugly check to make sure we have
                    # a json string
                    if data['courses'][:2] != "[{":
                        continue

                    site_details.courses = d['courses']

                # Add/commit the siteinfo_details we just retreived to the db
                g.db_session.add(site_details)
                g.db_session.commit()

        # Close the siteinfo_data result loop
        siteinfo_data.close()
    # Close the siteinfo_installed result loop
    siteinfo_installed.close()


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
                district_info[str(site.id)]['admin'] = details.adminemail
                district_info[str(site.id)]['teachers'] = details.teachers
                district_info[str(site.id)]['users'] = details.activeusers
                district_info[str(site.id)]['courses'] = (
                    len(json.loads(details.courses)) if details.courses else 0
                )

    return district_info


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
