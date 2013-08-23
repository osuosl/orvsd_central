from orvsd_central import db
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

sites_courses = db.Table('sites_courses',
                         db.Model.metadata,
                         db.Column('site_id',
                                   db.Integer,
                                   db.ForeignKey('sites.id',
                                                 use_alter=True,
                                                 name=
                                                 'fk_sites_courses_site_id')),
                         db.Column('course_id',
                                   db.Integer,
                                   db.ForeignKey('courses.id',
                                                 use_alter=True,
                                                 name=
                                                 'fk_sites_courses_course_id'))
                         )


class User(db.Model):
    """
    User model for ORVSD_CENTRAL
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.SmallInteger)
    #Possibly another column for current status

    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)

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

    def getRole(self):
        """
        returns the role for User
        """
        return USER.STATUS[self.status]

    def __repr__(self):
        return '<User %r>' % (self.name)

    def serialize(self):
        return { 'id' : self.id,
                 'name' : self.name,
                 'email' : self.email,
                 # Don't reveal passwords
                 'password' : '********',
                 'role' : self.role }

class District(db.Model):
    """
    Districts have many schools
    """

    __tablename__ = 'districts'
    id = db.Column(db.Integer, primary_key=True)
    # Full name of the district
    name = db.Column(db.String(255))
    # short name/abbreviation
    shortname = db.Column(db.String(255))
    # root path in which school sites are stored - maybe redundant
    base_path = db.Column(db.String(255))

    def __init__(self, name, shortname, base_path):
        self.name = name
        self.shortname = shortname
        self.base_path = base_path

    def __repr__(self):
        return "<Disctrict('%s')>" % (self.name)

    def get_properties(self):
        return ['id', 'name', 'shortname', 'base_path']

    def serialize(self):
        return { 'id' : self.id,
                 'name' : self.name,
                 'shortname' : self.shortname,
                 'base_path' : self.base_path }

class School(db.Model):
    """
    Schools belong to one district, have many sites and  many courses
    """

    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    # points to the owning district
    district_id = db.Column(db.Integer,
                            db.ForeignKey('districts.id',
                                          use_alter=True,
                                          name='fk_school_to_district_id'))
    # school name
    name = db.Column(db.String(255))
    # short name or abbreviation
    shortname = db.Column(db.String(255))
    # the base domain name for this school's sites (possibly redundant)
    domain = db.Column(db.String(255))
    # list of tokens indicating licenses for some courses - courses with
    # license tokens in this list can be installed in this school
    license = db.Column(db.String(255))
    # NEED TO FIND FLASK FOR THIS
    district = db.relationship("District",
                               backref=db.backref('schools', order_by=id))

    def __init__(self, name, shortname, domain, license):
        self.name = name
        self.shortname = shortname
        self.domain = domain
        self.license = license

    def get_properties(self):
        return ['id', 'disctrict_id', 'name', 'shortname', 'domain', 'license']

    def serialize(self):
        return { 'id' : self.id,
                 'district_id' : self.district_id,
                 'name' : self.name,
                 'shortname' : self.shortname,
                 'domain' : self.domain,
                 'license' : self.license }


class Site(db.Model):
    __tablename__ = 'sites'
    id = db.Column(db.Integer, primary_key=True)
    # points to the owning school
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id',
                                                    use_alter=True,
                                                    name="fk_sites_school_id"))
    # name of the site - (from siteinfo)
    name = db.Column(db.String(255))
    # (from siteinfo)
    sitetype = db.Column(db.Enum('moodle', 'drupal', name='site_types'))
    # moodle or drupal's base_url - (from siteinfo)
    baseurl = db.Column(db.String(255))
    # site's path on disk - (from siteinfo)
    basepath = db.Column(db.String(255))
    # is there a jenkins cron job? If so, when did it last run?
    jenkins_cron_job = db.Column(db.DateTime)
    # what machine is this on, or is it in the moodle cloud?
    location = db.Column(db.String(255))

    site_details = db.relationship("SiteDetail", backref=db.backref('sites'))
    courses = db.relationship("Course",
                              secondary='sites_courses',
                              backref='sites')

    def __init__(self, name, sitetype, baseurl,
                 basepath, jenkins_cron_job, location):
        self.name = name
        self.sitetype = sitetype
        self.baseurl = baseurl
        self.basepath = basepath
        self.jenkins_cron_job = jenkins_cron_job
        self.location = location

    def __repr__(self):
        return "<Site('%s','%s','%s','%s','%s')>" % (self.name,
                                                     self.sitetype,
                                                     self.baseurl,
                                                     self.basepath,
                                                     self.jenkins_cron_job)

    def get_properties(self):
        return ['id', 'school_id', 'name', 'sitetype',
                'baseurl', 'basepath', 'jenkins_cron_job', 'location']

    def serialize(self):
        return { 'id' : self.id,
                 'name' : self.name,
                 'sitetype' : self.sitetype,
                 'baseurl' : self.baseurl,
                 'basepath' : self.basepath,
                 'jenkins_cron_job' : self.jenkins_cron_job,
                 'location' : self.location }

class SiteDetail(db.Model):
    """
    Site_details belong to one site. This data is updated from the
    siteinfo tables, except the date - a new record is added with each
    update. See siteinfo notes.
    """

    __tablename__ = 'site_details'
    id = db.Column(db.Integer, primary_key=True)
    # points to the owning site
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id',
                                                  use_alter=True,
                                                  name=
                                                  'fk_site_details_site_id'))
    courses = db.Column(db.Text())
    siteversion = db.Column(db.String(255))
    siterelease = db.Column(db.String(255))
    adminemail = db.Column(db.String(255))
    totalusers = db.Column(db.Integer)
    adminusers = db.Column(db.Integer)
    teachers = db.Column(db.Integer)
    activeusers = db.Column(db.Integer)
    totalcourses = db.Column(db.Integer)
    timemodified = db.Column(db.DateTime)

    def __init__(self, siteversion, siterelease, adminemail,
                 totalusers, adminusers, teachers, activeusers,
                 totalcourses, timemodified):
        self.siteversion = siteversion
        self.siterelease = siterelease
        self.adminemail = adminemail
        self.totalusers = totalusers
        self.adminusers = adminusers
        self.teachers = teachers
        self.activeusers = activeusers
        self.totalcourses = totalcourses
        self.timemodified = timemodified

    def __repr__(self):
        return "<Site('%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % \
               (self.siteversion, self.siterelease, self.adminemail,
                self.totalusers, self.adminusers, self.teachers,
                self.activeusers, self.totalcourses, self.timemodified)

    def serialize(self):
        return { 'id' : self.id,
                 'site_id' : self.site_id,
                 'courses' : self.courses,
                 'siteversion' : self.siteversion,
                 'siterelease' : self.siterelease,
                 'adminemail' : self.adminemail,
                 'totalusers' : self.totalusers,
                 'adminusers' : self.adminusers,
                 'teachers' : self.teachers,
                 'activeusers' : self.activeusers,
                 'totalcourses' : self.totalcourses,
                 'timemodified' : self.timemodified }


class Course(db.Model):
    """
    Courses belong to many schools
    """

    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.Integer)
    name = db.Column(db.String(255))
    shortname = db.Column(db.String(255))
    # schools with a license token matching this can install this class
    license = db.Column(db.String(255))
    # moodle category for this class (probably "default")
    category = db.Column(db.String(255))
    source = db.Column(db.String(255))

    course_details = db.relationship("CourseDetail",
                                     backref=db.backref('course',
                                     order_by=id))

    def __init__(self, serial, name, shortname,
                 license=None, category=None, source=None):
        self.serial = serial
        self.name = name
        self.shortname = shortname
        self.license = license
        self.category = category
        self.source = source

    def __repr__(self):
        return "<Site('%s','%s','%s','%s','%s','%s')>" % \
               (self.serial, self.name, self.shortname,
                self.license, self.category, self.source)

    def get_properties(self):
        return ['id', 'serial', 'name', 'shortname', 'license', 'category']

    def serialize(self):
        return { 'id' : self.id,
                 'serial' : self.serial,
                 'name' : self.name,
                 'shortname' : self.shortname,
                 'license' : self.license,
                 'category' : self.category,
                 'source' : self.source }

class CourseDetail(db.Model):
    __tablename__ = 'course_details'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer,
                          db.ForeignKey('courses.id',
                                        use_alter=True,
                                        name='fk_course_details_site_id'))
    # just the name, with extension, no path
    filename = db.Column(db.String(255))
    # course version number (could be a string, ask client on format)
    version = db.Column(db.Float())
    # When the Course was last updated
    updated = db.Column(db.DateTime)
    active = db.Column(db.Boolean)
    moodle_version = db.Column(db.String(255))
    moodle_course_id = db.Column(db.Integer)

    def __init__(self, course_id, filename, version, updated,
                 active, moodle_version, moodle_course_id):
        self.course_id = course_id
        self.filename = filename
        self.version = version
        self.updated = updated
        self.active = active
        self.moodle_version = moodle_version
        self.moodle_course_id = moodle_course_id

    def __repr__(self):
        return "<CourseDetail('%s','%s','%s','%s','%s','%s')>" % \
               (self.course_id, self.filename, self.version,
                self.updated, self.active, self.moodle_version,
                self.moodle_course_id)

    def serialize(self):
        return { 'id' : self.id,
                 'course_id' : self.course_id,
                 'filename' : self.filename,
                 'version' : self.version,
                 'updated' : self.updated,
                 'active' : self.active,
                 'moodle_version' : self.moodle_version }
