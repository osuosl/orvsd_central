from flask import Flask, render_template, g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
import sqlite3


app = Flask(__name__) 
app.config.from_object('config')

lm = LoginManager()

db = SQLAlchemy(app)

import models

lm.setup_app(app)
@lm.user_loader
def load_user(userid):
    return User.get(userid)



@app.before_request
def before_request():
    g.db = db 

@app.teardown_request
def teardown_request(exception):
    g.db.db_session.remove()        

from views import userblp 
app.register_blueprint(userblp)
