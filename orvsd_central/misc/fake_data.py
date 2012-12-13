import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Table, Text, Float
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime, date, time, timedelta
from sqlite3 import dbapi2 as sqlite
from orvsd_central.models import User, District, School, Site, SiteDetail, Course, Course_Detail

"""
This just sets up the engine and points it at the server
replace "lamp" with your mysql server name after you have
created the orvsd_central table and user (use whatever
table and user names you like)
"""
engine = create_engine('sqlite+pysqlite:///orvsd_test.db', module=sqlite)
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
