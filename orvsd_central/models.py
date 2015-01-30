import hashlib
import json
import logging
import time

from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Integer, SmallInteger, String, Text)
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.declarative import declarative_base

from werkzeug.security import generate_password_hash, check_password_hash

Model = declarative_base()


class SiteCourse(Model):
    """
    A representation of the connection between the courses each site has
    installed, and information about those course details.

    site_id        : the site's id
    course_id      : the course's id
    celery_task_id : celery task id for the site
    """

    __tablename__ = 'sites_courses'

    id = Column(Integer, primary_key=True)
    site_id = Column(
        Integer,
        ForeignKey(
            'sites.id',
            use_alter=True,
            name='fk_sites_courses_site_id'
        )
    )
    course_id = Column(
        Integer,
        ForeignKey(
            'courses.id',
            use_alter=True,
            name='fk_sites_courses_course_id'
        )
    )
    celery_task_id = Column(String(255))

    def __init__(self, site_id, course_id, celery_task_id):
        self.site_id = site_id
        self.course_id = course_id
        self.celery_task_id = celery_task_id


class User(Model):
    """
    A Model representation of your average User.

    id       : the user's unique id
    name     : the user's unique name
    email    : the user's unique email
    password : the user's password information
    role     : 1 for standard users
               2 for helpdesk user
               3 for admins

    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    password = Column(String(768))
    role = Column(SmallInteger, default=1)
    # Possibly another column for current status

    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password=password,
                                               method='pbkdf2:sha512',
                                               salt_length=128)
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.name)

    def serialize(self):
        return {'id': self.id,
                'name': self.name,
                'email': self.email,
                # Don't reveal passwords
                'password': '********',
                'role': self.role}


class District(Model):
    """
    A Model representation of a District.
    * Districts have many schools.

    id        : The district's id
    state_id  : State given ID number
    name      : Full name of the district
    shortname : Short name or abbreviation
    base_path : Root path in which school sites are stored (maybe redundant)
    """
    __tablename__ = 'districts'

    id = Column(Integer, primary_key=True)
    state_id = Column(Integer)
    name = Column(String(255))
    shortname = Column(String(255))
    base_path = Column(String(255))

    def __repr__(self):
        return "<Disctrict('%s')>" % (self.name)

    def get_properties(self):
        return ['id', 'state_id', 'name', 'shortname', 'base_path']

    def serialize(self):
        return {'id': self.id,
                'state_id': self.state_id,
                'name': self.name,
                'shortname': self.shortname,
                'base_path': self.base_path}


class School(Model):
    """
    A Model representation of a School.
    * Schools belong to one district, may have many sites and courses.

    id          : The school id
    district_id : Points to the owning district
    state_id    : State assigned id
    name        : School name
    shortname   : Short name or abbreviation
    domain      : The base domain name for this school's sites (possibly redundant)
    license     : List of tokens indicating licenses for some courses - courses with
                  license tokens in this list can be installed in this school
    county      : The county the school belongs to
    district    : The district with which the school is associated
    """
    __tablename__ = 'schools'

    id = Column(Integer, primary_key=True)
    district_id = Column(Integer,
                         ForeignKey('districts.id',
                                    use_alter=True,
                                    name='fk_school_to_district_id'))
    state_id = Column(Integer)
    name = Column(String(255))
    shortname = Column(String(255))
    domain = Column(String(255))
    license = Column(String(255))
    county = Column(String(255))

    district = relationship("District",
                            backref=backref('schools', order_by=id))

    def get_properties(self):
        return ['id', 'disctrict_id', 'name', 'shortname', 'domain', 'license',
                'county']

    def serialize(self):
        return {'id': self.id,
                'district_id': self.district_id,
                'state_id': self.state_id,
                'name': self.name,
                'shortname': self.shortname,
                'domain': self.domain,
                'license': self.license,
                'county': self.county}


class Site(Model):
    """
    A Model respresentation of a Site.
    * Sites belong to one school, and may have many SiteDetails.

    school_id        : Points to the owning school
    name             : Name of the site - (from siteinfo)
    dev              : True if this a dev site, False by default
    sitetype         : From siteinfo
    baseurl          : Moodle or drupal's base url - (from siteinfo)
    basepath         : The site's path on disk - (from siteinfo)
    jenkins_cron_job : Last run of jenkins cron job, if there is one
    location         : What machine the site is on, or is it in the cloud
    moodle_tokens    : Moodle plugins - service -> token (json)
    """
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True)
    school_id = Column(Integer, ForeignKey('schools.id',
                                           use_alter=True,
                                           name="fk_sites_school_id"))
    name = Column(String(255))
    dev = Column(Boolean, default=False)
    sitetype = Column(Enum('moodle', 'drupal', name='site_types'))
    baseurl = Column(String(255))
    basepath = Column(String(255))
    jenkins_cron_job = Column(DateTime)
    location = Column(String(255))
    moodle_tokens = Column(String(2048))

    site_details = relationship("SiteDetail", backref=backref('sites'))
    courses = relationship("Course",
                           secondary='sites_courses',
                           backref='sites')

    def add_taken(self, service, token):
        """
        Add token for service to moodle_tokens
        """

        try:
            tokens = json.loads(self.moodle_tokens)
        except ValueError:
            logging.warn("%s's moodle_tokens was not JSON." % self.name)
            tokens = {}

        tokens[service] = token
        self.moodle_tokens = json.dumps(tokens)

    def remove_token(self, service):
        """
        Remove a service/token from the site's moodle_tokens
        """

        try:
            tokens = json.loads(self.moodle_tokens)
        except ValueError:
            logging.warn("%s's moodle_tokens was not JSON." % self.name)
            return

        if service in tokens.keys():
            del tokens[service]
            self.moodle_tokens = json.dumps(tokens)

    def get_token(self, service):
        """
        Retrieve a the moodle token for the service. Return None if no key
        is found
        """

        try:
            return json.loads(self.moodle_tokens).get(service, None)
        except ValueError:
            logging.warn("%s's moodle_tokens was not JSON." % self.name)

    def get_moodle_tokens(self):
        """
        Return a json.loads() object of moodle_tokens
        """

        try:
            tokens = json.loads(self.moodle_tokens)
        except ValueError:
            logging.warn("%s's moodle_tokens was not JSON." % self.name)
            tokens = {}

        return tokens

    def __repr__(self):
        return "<Site('%s','%s','%s','%s','%s','%s','%s')>" % \
               (self.name, self.school_id, self.dev, self.sitetype,
                self.baseurl, self.basepath, self.jenkins_cron_job)

    def get_properties(self):
        return ['id', 'school_id', 'name', 'sitetype',
                'baseurl', 'basepath', 'jenkins_cron_job', 'location']

    def serialize(self):
        return {'id': self.id,
                'school_id': self.school_id,
                'name': self.name,
                'dev': self.dev,
                'sitetype': self.sitetype,
                'baseurl': self.baseurl,
                'basepath': self.basepath,
                'jenkins_cron_job': self.jenkins_cron_job,
                'location': self.location,
                'moodle_tokens': self.moodle_tokens}


class SiteDetail(Model):
    """
    Site_details belong to one site. This data is updated from the
    siteinfo tables, except the date - a new record is added with each
    update. See siteinfo notes.

    courses      : A list of courses
    siteversion  : A moodle style version such as 2014121900
    siterelease  : Moodle version such as 2.7
    adminlist    : JSON object of current site admins
    teachers     : Number of teachers
    activeusers  : Number of active users
    totalcourses : Number of courses
    timemodified : Date set by the time of the call to util.gather_siteinfo()
    """
    __tablename__ = 'site_details'

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('sites.id',
                                         use_alter=True,
                                         name='fk_site_details_site_id'))
    courses = Column(Text())
    siteversion = Column(String(255))
    siterelease = Column(String(255))
    adminlist = Column(String(4096))
    totalusers = Column(Integer)
    adminusers = Column(Integer)
    teachers = Column(Integer)
    activeusers = Column(Integer)
    totalcourses = Column(Integer)
    timemodified = Column(DateTime)

    def __repr__(self):
        return ("<Site('%s','%s','%s','%s','%s',"
                "'%s','%s','%s','%s','%s','%s')>" % (
                   self.site_id,
                   self.courses,
                   self.siteversion,
                   self.siterelease,
                   self.adminlist,
                   self.totalusers,
                   self.adminusers,
                   self.teachers,
                   self.activeusers,
                   self.totalcourses,
                   self.timemodified
                )
        )

    def serialize(self):
        return {'id': self.id,
                'site_id': self.site_id,
                'courses': self.courses,
                'siteversion': self.siteversion,
                'siterelease': self.siterelease,
                'adminlist': self.adminlist,
                'totalusers': self.totalusers,
                'adminusers': self.adminusers,
                'teachers': self.teachers,
                'activeusers': self.activeusers,
                'totalcourses': self.totalcourses,
                'timemodified': self.timemodified}


class Course(Model):
    """
    A Model representation of a Course.
    * Courses belong to many schools

    id        : Uniquely identifies among instances or versions of a course
    serial    : Shared identifier among different versions of the same course
    name      : The course name (a moodle setting)
    shortname : The course short name (a moodle setting)
    license   : Schools with a license token matching this can install this class
    category  : Moodle category for this class (probably "default")
    source    : Provider of the course, possibly used by moodle for storing the location
    """
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    serial = Column(Integer)
    name = Column(String(255))
    shortname = Column(String(255))
    license = Column(String(255))
    category = Column(String(255))
    source = Column(String(255))

    course_details = relationship("CourseDetail",
                                  backref=backref('course', order_by=id))

    def __repr__(self):
        return "<Site('%s','%s','%s','%s','%s','%s')>" % \
               (self.serial, self.name, self.shortname,
                self.license, self.category, self.source)

    def get_properties(self):
        return ['id', 'serial', 'name', 'shortname', 'license', 'category']

    def serialize(self):
        return {'id': self.id,
                'serial': self.serial,
                'name': self.name,
                'shortname': self.shortname,
                'license': self.license,
                'category': self.category,
                'source': self.source}


class CourseDetail(Model):
    """
    A Model representation of a Course's details.

    id               : Unique to orvsd
    course_id        : Unique to orvsd
    filename         : The name and extension without the full path
    version          : The version, format determined by client
    updated          : Time of the last update
    active           : True if the course has recently been in use
    moodle_version   : A moodle style version
    moodle_course_id : The course id determined by moodle
    """
    __tablename__ = 'course_details'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer,
                       ForeignKey('courses.id',
                                  use_alter=True,
                                  name='fk_course_details_site_id'))
    filename = Column(String(255))
    version = Column(Float())
    updated = Column(DateTime)
    active = Column(Boolean)
    moodle_version = Column(String(255))
    moodle_course_id = Column(Integer)

    def __repr__(self):
        return "<CourseDetail('%s','%s','%s','%s','%s','%s','%s','%s')>" % \
               (self.course_id, self.filename, self.version, self.updated,
                self.active, self.moodle_version, self.source,
                self.moodle_course_version)

    def serialize(self):
        return {'id': self.id,
                'course_id': self.course_id,
                'filename': self.filename,
                'version': self.version,
                'updated': self.updated,
                'active': self.active,
                'moodle_version': self.moodle_version,
                'moodle_course_id': self.moodle_course_id}
