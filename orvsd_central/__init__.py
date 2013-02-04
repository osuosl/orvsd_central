from flask import Flask, render_template, g
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
db.init_app(app)



import models, views

@app.before_request
def before_request():
    g.db = db

