"""
Utility class containing useful methods not tied to specific models or views
"""
from oursql import connect, DictCursor
from orvsd_central import db, app
from models import District, School, Site, SiteDetail, Course, CourseDetail, User
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, date, time, timedelta
import json
import re
import datetime

class Util():
    def gather_siteinfo(self):
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
                            location = '.'.split(d['location'])[0]
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
                                        license='')
                        school.district_id = 0
                        db.session.add(school)
                        db.session.commit()

                    # find the site
                    site = Site.query.filter_by(baseurl=school_url).first()
                    # if no site exists, make a new one, school_id = school.id
                    if site is None:
                        site = Site(name=d['sitename'],   
                                    sitetype=d['sitetype'],
                                    baseurl='',
                                    basepath='',
                                    jenkins_cron_job=None,
                                    location='')
                    
                    site.school_id = school.id

                    site.baseurl = school_url
                    site.basepath = d['basepath']
                    site.location = location
                    db.session.add(site)
                    db.session.commit()

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
                            
                        """ @TODO: create the correct association model for this to work
                        courses = json.loads(d['courses'])
                        associated_courses = []

                        for i, course in enumerate(courses):
                            if course['serial'] != '0':
                                course_serial = course['serial'][:4]
                                orvsd_course = Course.query.filter_by(serial=course_serial).first()
                                if orvsd_course:
                                    # store this association
                                    # delete this course from the json string
                                    pass
                                     
                        # put all the unknown courses back in the 
                        # site_details record
                        site_details.courses = json.dumps(courses)
                        """

                        site_details.courses = d['courses']
                    
                    db.session.add(site_details)
                    db.session.commit()



