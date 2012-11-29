from orvsd_central import db
from orvsd_central import constants as USER
import sqlalchemy
from datetime import datetime, date, time, timedelta


class User(db.Model):
    """
    User model for ORVSD_CENTRAL
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(20))
    role = db.Column(db.SmallInteger, default = USER.HELPDESK)
#Possibly another column for current status

    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password

    def getRole(self):
        """
        returns the role for User
        """
        return USER.STATUS[self.status]

    def __repr__(self):
        return '<User %r>' % (self.name)


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
