"""
Utility class containing useful methods not tied to specific models or views
"""
from bs4 import BeautifulSoup as Soup
import datetime
import json
import os
import re
from datetime import datetime, date, time, timedelta
from functools import wraps

import requests
from flask import flash, session
from flask.ext.login import current_user
from oursql import connect, DictCursor

from orvsd_central import app, constants, celery, login_manager
from orvsd_central.database import db_session
from orvsd_central.models import (District, School, Site, SiteDetail,
                                  Course, CourseDetail, User)


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
        db_session.add(new_course)

        # Until the session is committed, the new_course does not yet have
        # an id.
        db_session.commit()

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

    db_session.add(new_course_detail)
    db_session.commit()

    #Get rid of moodle_backup.xml
    os.remove(project_folder+"moodle_backup.xml")


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


def gather_siteinfo():
    user = app.config['SITEINFO_DATABASE_USER']
    password = app.config['SITEINFO_DATABASE_PASS']
    address = app.config['SITEINFO_DATABASE_HOST']
    DEBUG = True

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

        # for each relevent database, pull the siteinfo data
        for database in db_sites:
            cherry = connect(user=user,
                             passwd=password,
                             host=address,
                             db=database[0])

            # use DictCursor here to get column names as well
            pie = cherry.cursor(DictCursor)

            # Grab the site info data
            pie.execute("select * from `%s`;" % database[1])
            data = pie.fetchall()
            cherry.close()

            # For all the data, shove it into the central db
            for d in data:
                # what version of moodle is this from?
                version = d['siterelease'][:3]

                # what is our school domain? take the protocol
                # off the baseurl
                school_re = 'http[s]{0,1}:\/\/'
                school_url = re.sub(school_re, '', d['baseurl'])

                # try to figure out what machine this site lives on
                if 'location' in d:
                    if d['location'][:3] == 'php':
                        location = 'platform'
                    else:
                        location = d['location']
                else:
                    location = 'unknown'

                # get the school
                school = School.query.filter_by(domain=school_url).first()
                # if no school exists, create a new one with
                # name = sitename, district_id = 0 (special 'Unknown'
                # district)
                if school is None:
                    school = School(name=d['sitename'],
                                    shortname=d['sitename'],
                                    domain=school_url,
                                    license='',
                                    state_id=None)
                    school.district_id = 0
                    db_session.add(school)
                    db_session.commit()

                # find the site
                site = Site.query.filter_by(baseurl=school_url).first()
                # if no site exists, make a new one, school_id = school.id
                if site is None:
                    site = Site(name=d['sitename'],
                                sitetype=d['sitetype'],
                                baseurl='',
                                basepath='',
                                jenkins_cron_job=None,
                                location='',
                                school_id=None)

                site.school_id = school.id

                site.baseurl = school_url
                site.basepath = d['basepath']
                site.location = location
                db_session.add(site)
                db_session.commit()

                # create new site_details table
                # site_id = site.id, timemodified = now()
                now = datetime.datetime.now()
                site_details = SiteDetail(siteversion=d['siteversion'],
                                          siterelease=d['siterelease'],
                                          adminemail=d['adminemail'],
                                          totalusers=d['totalusers'],
                                          adminusers=d['adminusers'],
                                          teachers=d['teachers'],
                                          activeusers=d['activeusers'],
                                          totalcourses=d['totalcourses'],
                                          timemodified=now)
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

                db_session.add(site_details)
                db_session.commit()


def get_course_folders(base_path):
    folders = ['None']
    for root, sub_folders, files in os.walk(base_path):
        for folder in sub_folders:
            if folder not in folders:
                folders.append(folder)
    return folders


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


# /base_path/source/path is the format of the parsed directories.
def get_path_and_source(base_path, file_path):
    path = file_path.strip(base_path).partition('/')
    return path[0]+'/', path[2]


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


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


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


# Decorator for defining access to certain actions.
# 1 - General User (Implicit with login_required)
# 2 - Help Desk
# 3 - Admin
def requires_role(role):
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
