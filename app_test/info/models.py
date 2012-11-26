import sqlalchemy
from app_test import db
from datetime import datetime, date, time, timedelta

sites_courses = db.Table('sites_courses', db.Model.metadata,
   db.Column('site_id', db.Integer, db.ForeignKey('sites.id')),
   db.Column('course_id', db.Integer, db.ForeignKey('courses.id')))


"""
Districts have many schools
"""
class District(db.Model):
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
    return "<Disctrict('%s','%s')>" % (self.name)

"""
Schools belong to one district, have many sites and  many courses
"""
class School(db.Model):
  __tablename__ = 'schools'
  id = db.Column(db.Integer, primary_key=True)
  # points to the owning district
  disctrict_id = db.Column(db.Integer, db.ForeignKey('districts.id'))
  # school name
  name = db.Column(db.String(255)) 
  # short name or abbreviation
  shortname = db.Column(db.String(255))
  # the base domain name for this school's sites (possibly redundant) 
  domain = db.Column(db.String(255))
  # list of tokens indicating licenses for some courses - courses with 
  # license tokens in this list can be installed in this school
  license = db.Column(db.String(255)) 

  district = db.relationship("District", backref=db.backref('schools', order_by=id)) #NEED TO FIND FLASK FOR THIS

  def __init__(self, name, shortname, domain, license):
    self.name = name
    self.shortname = shortname
    self.domain = domain
    self.license = license

  def __repr__(self):
    return "<Site('%s','%s','%s')>" % (self.name, self.domain, self.license)

"""
Sites belong to one school, have many site_details, and many courses
Some of the fields come from the siteinfo tables, see siteinfo notes
"""
class Site(db.Model):
  __tablename__ = 'sites'
  id = db.Column(db.Integer, primary_key=True)
  # points to the owning school
  school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))
  # name of the site - (from siteinfo)
  sitename = db.Column(db.String(255)) 
  sitetype = db.Column(db.Enum('moodle','drupal', name='site_types')) # (from siteinfo)
  # moodle or drupal's base_url - (from siteinfo)
  baseurl = db.Column(db.String(255)) 
  # site's path on disk - (from siteinfo)
  basepath = db.Column(db.String(255)) 
  # is there a jenkins cron job? If so, when did it last run?
  jenkins_cron_job = db.Column(db.DateTime) 
  # what machine is this on, or is it in the moodle cloud?
  location = db.Column(db.String(255)) 

  school = db.relationship("School", backref=db.backref('sites', order_by=id))
  courses = db.relationship("Course", secondary=sites_courses, backref='sites')

  def __init__(self, sitename, sitetype, baseurl, basepath, jenkins_cron_job, location):
    self.sitename = sitename
    self.sitetype = sitetype
    self.baseurl = baseurl
    self.basepath = basepath
    self.jenkins_cron_job = jenkins_cron_job
    self.location = location


  def __repr__(self):
    return "<Site('%s','%s','%s','%s','%s')>" % (self.sitename, self.sitetype, self.baseurl, self.basepath, self.jenkins_cron_job)

"""
Site_details belong to one school. This data is updated from the 
siteinfo tables, except the date - a new record is added with each
update. See siteinfo notes.
"""
class SiteDetail(db.Model):
  __tablename__ = 'site_details'
  id = db.Column(db.Integer, primary_key=True)
  # points to the owning site
  site_id = db.Column(db.Integer, db.ForeignKey('sites.id'))
  siteversion = db.Column(db.String(255))
  siterelease = db.Column(db.String(255))
  adminemail = db.Column(db.String(255))
  totalusers = db.Column(db.Integer)
  adminusers = db.Column(db.Integer)
  teachers = db.Column(db.Integer)
  activeusers = db.Column(db.Integer)
  totalcourses = db.Column(db.Integer)
  timemodified = db.Column(db.DateTime)

  school = db.relationship("Site", backref=db.backref('site_details', order_by=id))

  def __init__(self, siteversion, siterelease, adminemail, totalusers, adminusers, teachers, activeusers, totalcourses, timemodified):
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
    return "<Site('%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.siteversion, self.siterelease, self.adminemail, self.totalusers, self.adminusers, self.teachers, self.activeusers, self.totalcourses, self.timemodified)

"""
Courses belong to many schools
"""
class Course(db.Model):
  __tablename__ = 'courses'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  shortname = db.Column(db.String(255))
  # just the name, with extension, no path
  filename = db.Column(db.String(255))
  # schools with a license token matching this can install this class 
  license = db.Column(db.String(255)) 
  # moodle category for this class (probably "default")
  category = db.Column(db.String(255))
  # course version number (could be a string, ask client on format)
  version = db.Column(db.Float()) 
  #number of installations of this course
  num_installs = db.Column(db.Integer)
  #number of users
  num_users = db.Column(db.Integer)
  def __init__(self, name, shortname, filename, license, category, version):
    self.name = name
    self.shortname = shortname
    self.filename = filename
    self.license = license
    self.category = category
    self.version = version

  def __repr__(self):
    return "<Site('%s','%s','%s','%s','%s','%s')>" % (self.name, self.shortname, self.filename, self.license, self.category, self.version)
