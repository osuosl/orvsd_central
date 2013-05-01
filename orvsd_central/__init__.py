from flask import Flask, render_template, g
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.oauth import OAuth
from flask.ext.principal import Principal, Permission, RoleNeed


app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.setup_app(app)


principals = Principal(app)
add_permission = Permission(RoleNeed('add'))
load_permission = Permission(RoleNeed('load'))

# add permission is used to manually add data into the db
add_permission = Permission(RoleNeed('add'))

# load permission is used for future use, as we currently have
# no features specific to admin that helpdesk does not also have
load_permission = Permission(RoleNeed('load'))

# give permission to view information
view_permission = Permission(RoleNeed('view'))


oauth = OAuth()
google = oauth.remote_app(
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
    consumer_key=app.config['GOOGLE_CLIENT_ID'],
    consumer_secret=app.config['GOOGLE_CLIENT_SECRET'])


import models
import views


@app.before_request
def before_request():
    g.db = db
