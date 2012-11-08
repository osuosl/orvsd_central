import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Table, Text, Float
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime, date, time, timedelta
from sqlite3 import dbapi2 as sqlite

"""
This just sets up the engine and points it at the server
replace "lamp" with your mysql server name after you have 
created the orvsd_central table and user (use whatever 
table and user names you like)
"""
engine = create_engine('sqlite+pysqlite:///orvsd.db', module=sqlite)
Session = sessionmaker(bind=engine)
Base = declarative_base()

"""
This is a join table, it is just used for the many-to-many
relationship between courses and sites. It has no class, but
is referred to in the relationship declarations of course and
site
"""
sites_courses = Table('sites_courses', Base.metadata,
  Column('site_id', Integer, ForeignKey('sites.id')),
  Column('course_id', Integer, ForeignKey('courses.id'))
)

"""
Districts have many schools
"""
class District(Base):
  __tablename__ = 'districts'
  id = Column(Integer, primary_key=True)
  # Full name of the district
  name = Column(String(255))
  # short name/abbreviation
  shortname = Column(String(255)) 
  # root path in which school sites are stored - maybe redundant
  base_path = Column(String(255)) 

  def __init__(self, name, shortname, base_path):
    self.name = name
    self.shortname = shortname
    self.base_path = base_path
  def __repr__(self):
    return "<Disctrict('%s','%s')>" % (self.name)

"""
Schools belong to one district, have many sites and  many courses
"""
class School(Base):
  __tablename__ = 'schools'
  id = Column(Integer, primary_key=True)
  # points to the owning district
  district_id = Column(Integer, ForeignKey('districts.id'))
  # school name
  name = Column(String(255)) 
  # short name or abbreviation
  shortname = Column(String(255))
  # the base domain name for this school's sites (possibly redundant) 
  domain = Column(String(255))
  # list of tokens indicating licenses for some courses - courses with 
  # license tokens in this list can be installed in this school
  license = Column(String(255)) 

  district = relationship("District", backref=backref('schools', order_by=id))

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
class Site(Base):
  __tablename__ = 'sites'
  id = Column(Integer, primary_key=True)
  # points to the owning school
  school_id = Column(Integer, ForeignKey('schools.id'))
  # name of the site - (from siteinfo)
  sitename = Column(String(255)) 
  sitetype = Column(Enum('moodle','drupal', name='site_types')) # (from siteinfo)
  # moodle or drupal's base_url - (from siteinfo)
  baseurl = Column(String(255)) 
  # site's path on disk - (from siteinfo)
  basepath = Column(String(255)) 
  # is there a jenkins cron job? If so, when did it last run?
  jenkins_cron_job = Column(DateTime) 
  # what machine is this on, or is it in the moodle cloud?
  location = Column(String(255)) 

  school = relationship("School", backref=backref('sites', order_by=id))
  courses = relationship("Course", secondary=sites_courses, backref='sites')

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
class SiteDetail(Base):
  __tablename__ = 'site_details'
  id = Column(Integer, primary_key=True)
  # points to the owning site
  site_id = Column(Integer, ForeignKey('sites.id'))
  siteversion = Column(String(255))
  siterelease = Column(String(255))
  adminemail = Column(String(255))
  totalusers = Column(Integer)
  adminusers = Column(Integer)
  teachers = Column(Integer)
  activeusers = Column(Integer)
  totalcourses = Column(Integer)
  timemodified = Column(DateTime)

  school = relationship("Site", backref=backref('site_details', order_by=id))

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
class Course(Base):
  __tablename__ = 'courses'
  id = Column(Integer, primary_key=True)
  name = Column(String(255))
  shortname = Column(String(255))
  # just the name, with extension, no path
  filename = Column(String(255))
  # schools with a license token matching this can install this class 
  license = Column(String(255)) 
  # moodle category for this class (probably "default")
  category = Column(String(255))
  # course version number (could be a string, ask client on format)
  version = Column(Float()) 

  def __init__(self, name, shortname, filename, license, category, version):
    self.name = name
    self.shortname = shortname
    self.filename = filename
    self.license = license
    self.category = category
    self.version = version

  def __repr__(self):
    return "<Site('%s','%s','%s','%s','%s','%s')>" % (self.name, self.shortname, self.filename, self.license, self.category, self.version)


"""
Start a session and create all the tables based on the classes
we just defined
"""
session = Session()
Base.metadata.create_all(engine)

"""
seed with some test data:

Check with the client to make sure this test data is in the 
correct form and reflects the data that will be used in production

at some point this should be moved into a fixture file for consistent
testing
"""

#(name, shortname, base_path)
district1 = District('District1', 'D1', '/var/www/district1')
district2 = District('District2', 'D1', '/var/www/district2')
district3 = District('District3', 'D1', '/var/www/district3')

#(name, shortname, domain, license)
school1 = School('school1', 's1', 'www.school1.com', 'none' )
school2 = School('school2', '', 'www.school2.com', 'none' )
school3 = School('school3', 's3', 'www.school3.com', 'none' )
school4 = School('school4', 's4', 'www.school4.com', 'none' )
school5 = School('school5', '', 'www.school5.com', 'none' )
school6 = School('school6', 's6', 'www.school6.com', 'none' )

# assign the schools to some districts
district1.schools = [school1, school3, school5]
district2.schools = [school2]
district3.schools = [school4, school6]

# (sitename, sitetype, baseurl, basepath, jenkins_cron_job, location)
site1 = Site('school1 site1', 'drupal',  'http://www.school1.com/drupal', '/var/wwww/District1/school1/drupal', datetime.now(), 'yin')
site2 = Site('school1 site2', 'moodle',  'http://www.school1.com/moodle', '/var/wwww/District1/school1/moodle', datetime.now(), 'yin')
site3 = Site('school2 site1', 'moodle',  'http://www.school2.com/moodle', '/var/wwww/District2/school2/moodle', datetime.now(), 'virtual')
site4 = Site('school3 site1', 'moodle',  'http://www.school3.com/moodle', '/var/wwww/District1/school3/moodle', datetime.now(), 'yin')
site5 = Site('school4 site1', 'drupal',  'http://www.school4.com/drupal', '/var/wwww/District3/school4/drupal', datetime.now(), 'yin')
site6 = Site('school4 site2', 'moodle',  'http://www.school4.com/moodle', '/var/wwww/District3/school4/moodle', datetime.now(), 'yin')
site7 = Site('school5 site1', 'moodle',  'http://www.school5.com/drupal', '/var/wwww/District1/school1/moodle', datetime.now(), 'virtual')
site8 = Site('school6 site1', 'moodle',  'http://www.school6.com/drupal', '/var/wwww/District3/school6/moodle', datetime.now(), 'virtual')
site9 = Site('school6 site2', 'drupal',  'http://www.school6.com/drupal', '/var/wwww/District3/school6/drupal', datetime.now(), 'virtual')

# assign the sites to their schools
school1.sites = [site1, site2]
school2.sites = [site3]
school3.sites = [site4]
school4.sites = [site5, site6]
school5.sites = [site7]
school6.sites = [site8, site9]

# (name, shortname, filename, license, category, version)
course1 = Course('course1', 'c1', 'c1.zip', 'none', 'misc', 1.9)
course2 = Course('course2', 'c2', 'c2.zip', 'none', 'misc', 2.0)
course3 = Course('course3', 'c3', 'c3.zip', 'none', 'misc', 1)
course4 = Course('course4', 'c4', 'c4.zip', 'none', 'misc', 18.1)
course5 = Course('course5', 'c5', 'c5.zip', 'none', 'misc', 2.1)
course6 = Course('course6', 'c6', 'c6.zip', 'none', 'misc', 1.78)

# assign courses to sites (only moodle sites!)
site2.courses = [course1, course2, course3, course4]
site3.courses = [course2, course3, course5, course6]
site4.courses = [course1, course3, course4, course5, course6]
site6.courses = [course2]
site7.courses = [course1, course2, course3]
site8.courses = [course4, course5, course6]

#(siteversion, siterelease, adminemail, totalusers, adminusers, teachers, activeusers, totalcourses, timemodified)
site_details1 = SiteDetail('2.3','beta1','admin@school.edu',45,2,34,1,34,datetime.now() - timedelta(7))
site_details2 = SiteDetail('2.3','beta1','admin@school.edu',46,2,34,10,34,datetime.now()- timedelta(6))
site_details3 = SiteDetail('2.3','beta1','admin@school.edu',47,3,34,20,34,datetime.now()- timedelta(5))
site_details4 = SiteDetail('2.3','beta1','admin@school.edu',48,3,35,34,34,datetime.now()- timedelta(4))
site_details5 = SiteDetail('2.3','beta1','admin@school.edu',49,3,35,67,36,datetime.now()- timedelta(3))
site_details6 = SiteDetail('2.3','beta1','admin@school.edu',50,4,35,300,36,datetime.now()- timedelta(2))
site_details7 = SiteDetail('2.3','beta1','admin@school.edu',51,5,35,1500,36,datetime.now()- timedelta(1))
site_details8 = SiteDetail('2.3','beta1','admin@school.edu',51,5,35,1520,36,datetime.now())

#assign these site details to a (moodle) site - drupal has the same fields, but many are blank
site6.site_details = [site_details1, site_details2, site_details3, site_details4, site_details5, site_details6, site_details7, site_details8]

# add this stuff to the session (relationships cascade)
session.add_all([district1,district2,district3])

# commit the session, which actually writes all this to the db.
session.commit()

"""
When creating the migration to install this schema, for the reverse migration, a table drop shoudl be sufficient.
"""
