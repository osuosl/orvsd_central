import StringIO
import datetime
import json
import os
import re
import subprocess
import requests
from requests.exceptions import HTTPError
import zipfile

from bs4 import BeautifulSoup as Soup
import celery
from celery.utils.encoding import safe_repr, safe_str
from flask import (request, render_template, flash, g, session, redirect,
                   url_for, abort, jsonify)
from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from sqlalchemy import func, and_
from sqlalchemy.orm import eagerload
from sqlalchemy.sql.expression import desc
from werkzeug import check_password_hash, generate_password_hash

from orvsd_central import app, celery, constants, db, google, login_manager
from orvsd_central.forms import LoginForm, AddUser, InstallCourse
from orvsd_central.models import (District, School, Site, SiteDetail,
                                  Course, CourseDetail, User)
from orvsd_central.util import (get_obj_by_category, get_obj_identifier,
                                requires_role)


"""
HELPERS
"""


@app.route("/courses/update", methods=['GET', 'POST'])
@requires_role('helpdesk')
@login_required
def update_courselist():
    """
        Updates the database to contain the most recent course
        and course detail entries, based on available files.
    """
    num_courses = 0
    base_path = "/data/moodle2-masters/"
    mdl_files = []
    if request.method == "POST":
        # Get a list of all moodle course files
        # for source in os.listdir(base_path):
        for root, sub_folders, files in os.walk(base_path):
            for file in files:
                full_file_path = os.path.join(root, file)
                if os.path.isfile(full_file_path):
                    mdl_files.append(full_file_path)

        filenames = []
        sources = []
        for filename in mdl_files:
            source, path = get_path_and_source(base_path, filename)
            sources.append(source)
            filenames.append(path)

        details = db.session.query(CourseDetail) \
            .join(CourseDetail.course) \
            .filter(CourseDetail.filename.in_(
                    filenames)).all()

        for detail in details:
            if detail.filename in filenames:
                sources.pop(filenames.index(detail.filename))
                filenames.pop(filenames.index(detail.filename))

        for source, file_path in zip(sources, filenames):
            create_course_from_moodle_backup(base_path, source, file_path)
            num_courses += 1

        if num_courses > 0:
            flash(str(num_courses) + ' new courses added successfully!')
    return render_template('update_courses.html', user=current_user)


# /base_path/source/path is the format of the parsed directories.
def get_path_and_source(base_path, file_path):
    path = file_path.strip(base_path).partition('/')
    return path[0]+'/', path[2]


def create_course_from_moodle_backup(base_path, source, file_path):
    # Needed to delete extracted xml once operation is done
    project_folder = "/home/vagrant/orvsd_central/"

    # Unzip the file to get the manifest (All course backups are zip files)
    zip = zipfile.ZipFile(base_path+source+file_path)
    xmlfile = file(zip.extract("moodle_backup.xml"), "r")
    xml = Soup(xmlfile.read(), "xml")
    info = xml.moodle_backup.information

    old_course = Course.query.filter_by(
        name=info.original_course_fullname.string) or \
        Course.query.filter_by(
            name=info.original_course_shortname.string)

    if old_course is not None:
        # Create a course since one is unable to be found with that name.
        new_course = Course(serial=1000 + len(Course.query.all()),
                            source=source.replace('/', ''),
                            name=info.original_course_fullname.string,
                            shortname=info.original_course_shortname.string)
        db.session.add(new_course)

        # Until the session is committed, the new_course does not yet have
        # an id.
        db.session.commit()

        course_id = new_course.id
    else:
        course_id = old_course.id

    _version_re = re.findall(r'_v(\d)_', file_path)

    # Regex will only be a list if it has a value in it
    version = _version_re[0] if list(_version_re) else None

    new_course_detail = CourseDetail(course_id=course_id,
                                     filename=file_path,
                                     version=version,
                                     updated=datetime.datetime.now(),
                                     active=True,
                                     moodle_version=info.moodle_release.string,
                                     moodle_course_id=info
                                                     .original_course_id
                                                     .string)

    db.session.add(new_course_detail)
    db.session.commit()

    #Get rid of moodle_backup.xml
    os.remove(project_folder+"moodle_backup.xml")
