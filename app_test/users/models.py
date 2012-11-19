from app_test import db
from app_test.users import constants as USER

class User(db.Model):
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
        return USER.STATUS[self.status]

    def __repr__(self):
        return '<User %r>' % (self.name)
