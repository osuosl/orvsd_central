from flask import Flask, render_template, g
from flask.ext.login import LoginManager, current_user
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.oauth import OAuth
from celery import Celery

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.setup_app(app)

def init_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = init_celery(app)

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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', user=current_user), 404


from orvsd_central.controllers import general
from orvsd_central.controllers import report

app.register_blueprint(general.mod)
app.register_blueprint(report.mod)
