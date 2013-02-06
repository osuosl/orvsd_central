from flask import Flask, render_template, g
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.setup_app(app)


import models, views

@app.before_request
def before_request():
    g.db = db

