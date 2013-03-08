from flask import Flask, render_template, g
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.oauth import OAuth


app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.setup_app(app)


<<<<<<< HEAD
import models
import views

=======
oauth = OAuth()
google = oauth.remote_app('google',
                            base_url = 'https://www.google.com/accounts/',
                            authorize_url='https://accounts.google.com/o/oauth2/auth',
                            request_token_url=None,
                            request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email', 'response_type': 'code'},
                            access_token_url='https://accounts.google.com/o/oauth2/token',
                            access_token_method='POST',
                            access_token_params={'grant_type': 'authorization_code'},
                            consumer_key=app.config['GOOGLE_CLIENT_ID'],
                            consumer_secret=app.config['GOOGLE_CLIENT_SECRET'])
                


import models, views
>>>>>>> got google login with access token working

@app.before_request
def before_request():
    g.db = db
