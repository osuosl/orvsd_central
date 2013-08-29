from flask import (request, render_template, flash, g, session, redirect,
                   url_for, abort, jsonify)
from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from werkzeug import check_password_hash, generate_password_hash
from orvsd_central import db, app, login_manager, google
from forms import (LoginForm, AddDistrict, AddSchool, AddUser,
                   InstallCourse, AddCourse)
from models import (District, School, Site, SiteDetail,
                    Course, CourseDetail, User)
from sqlalchemy import func
from sqlalchemy.sql.expression import desc
from models import (District, School, Site, SiteDetail,
                    Course, CourseDetail, User)
import urllib2
import json
import re
import subprocess
import StringIO
import requests
import urllib


"""
ACCESS
"""


@app.route("/register", methods=['GET', 'POST'])
#@login_required
def register():
    #user=current_user
    form = AddUser()
    message = ""

    if request.method == "POST":
        if form.password.data != form.confirm_pass.data:
            message = "The passwords provided did not match!\n"
        elif not re.match('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$',
                          form.email.data):
            message = "Invalid email address!\n"
        else:
            # Add user to db
            db.session.add(User(name=form.user.data,
                                email=form.email.data,
                                password=form.password.data))
            db.session.commit()
            message = form.user.data+" has been added successfully!\n"

    return render_template('add_user.html', form=form,
                           message=message, user=current_user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(name=form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.")
            return redirect("/report")
        else:
            flash("Username/Password combo was not recognized.  "
                  "Please try again.")
    return render_template("login.html", form=form)


@app.route("/google_login")
def google_login():
    access_token = session.get('access_token')
    if access_token is None:
        callback = url_for('authorized', _external=True)
        return google.authorize(callback=callback)
    else:
        access_token = access_token
        headers = {'Authorization': 'OAuth '+access_token}
        req = urllib2.Request('https://www.googleapis.com/oauth2/v1/userinfo',
                              None, headers)
        try:
            res = urllib2.urlopen(req)
        except urllib2.URLError, e:
            if e.code == 401:
                session.pop('access_token', None)
                flash('There was a problem with your Google \
                      login information.  Please try again.')
                return redirect(url_for('login'))
            return res.read()
        obj = json.loads(res.read())
        email = obj['email']
        user = User.query.filter_by(email=email).first()
        #pop access token so it isn't sitting around in our
        #session any longer than nescessary
        session.pop('access_token', None)
        if user is not None:
            login_user(user)
            return redirect(url_for('report'))
        else:
            flash("This google account was not recognized \
                  as having access. Sorry.")
            return redirect(url_for('login'))


@app.route(app.config['REDIRECT_URI'])
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token
    return redirect(url_for('google_login'))


@app.route('/me')
@login_required
def home():
    """
    Loads a users home information page
    """
    #not sure current_user works this way, write test
    return render_template('users/templates/profile.html', user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


"""
ADD
"""


@app.route("/add/district", methods=['GET', 'POST'])
def add_district():
    form = AddDistrict()
    user = current_user
    if request.method == "POST":
        #Add district to db.
        db.session.add(District(form.name.data,
                                form.shortname.data,
                                form.base_path.data))
        db.session.commit()

    return render_template('add_district.html', form=form, user=user)


@login_required
@app.route("/add/school", methods=['GET', 'POST'])
def add_school():
    form = AddSchool()
    user = current_user
    msg = ""

    if request.method == "POST":
        #The district_id is supposed to be an integer
        #try:
            #district = District.query.filter_by(id=int(form.district_id))
            #                                          .all()
            #if len(district) == 1:
                #Add School to db
        db.session.add(School(int(form.district_id.data),
                              form.name.data, form.shortname.data,
                              form.domain.data. form.license.data))
        db.session.commit()
            #else:
            #    error_msg= "A district with that id doesn't exist!"
        #except:
        #    error_msg= "The entered district_id was not an integer!"
    return render_template('add_school.html', form=form,
                           msg=msg, user=user)


@app.route("/add/course", methods=['GET', 'POST'])
def add_course():
    form = AddCourse()
    user = current_user
    msg = ""
    if request.method == "POST":
        db.session.add(Course(int(form.serial.data), form.name.data,
                              form.shortname.data, form.license.data,
                              form.category.data))
        db.session.commit()
        msg = "Course: "+form.name.data+"added successfully!"

    return render_template('add_course.html', form=form, msg=msg, user=user)


"""
INSTALL
"""


@app.route('/install/course', methods=['GET', 'POST'])
def install_course():

    if request.method == 'GET':
        form = InstallCourse()

        # Get all the available course modules
        all_courses = CourseDetail.query.all()

        # Generate the list of choices for the template
        choices = []

        for course in all_courses:
            choices.append((course.course_id,
                            "%s - Version: %s - Moodle Version: %s" %
                            (course.course.name, course.version,
                             course.moodle_version)))

        form.course.choices = choices

        return render_template('install_course.html',
                               form=form, user=current_user)

    elif request.method == 'POST':
        # An array of unicode strings will be passed, they need to be integers
        # for the query
        selected_courses = [int(cid) for cid in request.form.getlist('course')]

        # The site to install the courses
        site = "%s/webservice/rest/server.php?wstoken=%s&wsfunction=%s" % (
               request.form.get('site'),
               app.config['INSTALL_COURSE_WS_TOKEN'],
               app.config['INSTALL_COURSE_WS_FUNCTION'])
        site = str(site.encode('utf-8'))

        # The CourseDetail objects of info needed to generate the url
        courses = CourseDetail.query.filter(CourseDetail
                                            .course_id.in_(selected_courses))\
                                    .all()

        # Appended to buy all the courses being installed
        output = ''

        # Loop through the courses, generate the command to be run, run it, and
        # append the ouput to output
        #
        # Currently this will break ao our db is not setup correctly yet
        for course in courses:
            # To get the file path we need the text input, the lowercase of
            # source, and the filename
            fp = app.config['INSTALL_COURSE_FILE_PATH']
            fp += course.source.lower() + '/'

            data = {'filepath': fp,
                    'file': course.filename,
                    'courseid': course.course_id,
                    'coursename': course.course.name,
                    'shortname': course.course.shortname,
                    'category': '1',
                    'firstname': 'orvsd',
                    'lastname': 'central',
                    'city': 'none',
                    'username': 'admin',
                    'email': 'a@a.aa',
                    'pass': 'testo123'}

            postdata = urllib.urlencode(data)

            resp = urllib.urlopen(site, data=postdata)

            output += "%s\n\n%s\n\n\n" % (course.course.shortname, resp.read())

        return render_template('install_course_output.html',
                               output=output,
                               user=current_user)


"""
VIEW
"""


@app.route('/view/schools/<int:school_id>', methods=['GET'])
@login_required
def view_school(school_id):

    school = School.query.filter_by(id=school_id).first()

    # Info for the school's page
    admins = 0
    teachers = 0
    users = 0

    # Get the school's sites
    sites = Site.query.filter_by(school_id=school_id).all()

    # School view template
    t = app.jinja_env.get_template('views/school.html')

    # if we have sites, grab the details needed for the template
    if sites:
        for site in sites:
            detail = SiteDetail.query.filter_by(site_id=site.id) \
                                     .order_by(SiteDetail
                                               .timemodified.desc()) \
                                     .first()
            if detail:
                admins += detail.adminusers
                teachers += detail.teachers
                users += detail.totalusers

    # Return a pre-compiled template to be dumped into the view template
    template = t.render(name=school.name, admins=admins, teachers=teachers,
                        users=users, user=current_user)

    return render_template('view.html', content=template, user=current_user)


# View courses installed for a specific school
@app.route('/view/schools/<int:school_id>/courses', methods=['GET'])
@login_required
def view_school_courses(school_id):
    school = School.query.filter_by(id=school_id).first()

    # Info for the school's page
    admins = 0
    teachers = 0
    users = 0

    # Get the school's sites
    sites = Site.query.filter_by(school_id=school_id).all()

    # School view template
    t = app.jinja_env.get_template('views/courses.html')

    # if we have sites, grab the details needed for the template
    if sites:
        for site in sites:
            detail = SiteDetail.query.filter_by(site_id=site.id) \
                                     .order_by(SiteDetail
                                               .timemodified.desc()) \
                                     .first()
            if detail:
                admins += detail.adminusers
                teachers += detail.teachers
                users += detail.totalusers

    # Get course list
    resp = requests.get('http://localhost:5555/api/tasks').json()
    course_details = [{'uuid': v['uuid'],
                       'task_state': v['state'],
                       'time_completed': datetime.datetime.fromtimestamp(int(v['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'),
                       'course_state': Soup(v['result']).find('message').get_text()}
                      for k, v in resp.iteritems()]

    # Sort course_details by timestamp.
    course_details = sorted(course_details, key=lambda course: course['time_completed'])

    # Return a pre-compiled template to be dumped into the view template
    template = t.render(name=school.name, admins=admins, teachers=teachers,
                        users=users, user=current_user, course_list=course_details)

    return render_template('view.html', content=template, user=current_user)


@app.route('/report/get_schools', methods=['POST'])
def get_schools():
    # From the POST, we need the district id, or distid
    dist_id = request.form.get('distid')

    # Given the distid, we get all the schools
    if dist_id:
        schools = School.query.filter_by(district_id=dist_id) \
                              .order_by("name").all()
    else:
        schools = School.query.order_by("name").all()

    # the dict to be jsonify'd
    school_list = {}

    for school in schools:
        school_list[school.shortname] = {'name': school.name, 'id': school.id}

    # Returned the jsonify'd data of counts and schools for jvascript to parse
    return jsonify(schools=school_list, counts=district_details(schools))


"""
REPORT
"""


@app.route("/report", methods=['GET'])
@login_required
def report():
    all_districts = District.query.order_by("name").all()
    dist_count = len(all_districts)
    school_count = School.query.count()
    site_count = Site.query.count()
    course_count = Course.query.count()

    inner = ""
    accord_id = "dist_accord"
    dist_id = "distid=%s"

    data = build_accordion(all_districts, accord_id, "district", dist_id)

    return render_template("report.html",
                           datadump=data,
                           dist_count=dist_count,
                           school_count=school_count,
                           site_count=site_count,
                           course_count=course_count,
                           user=current_user)


@app.route('/')
@login_required
def root():
    if not current_user.is_anonymous():
        return redirect(url_for('report'))
    return redirect(url_for('login'))

"""
REMOVE
"""


@app.route("/display/<category>")
def remove(category):
    user = get_user()
    obj = get_obj_by_category(category)
    if obj:
        objects = obj.query.all()
        if objects:
            # fancy way to get the properties of an object
            properties = objects[0].get_properties()
            return render_template('removal.html', category=category,
                                   objects=objects, properties=properties,
                                   user=user)

    abort(404)


@app.route("/remove/<category>", methods=['POST'])
def remove_objects(category):
    obj = get_obj_by_category(category)
    remove_ids = request.form.getlist('remove')
    for remove_id in remove_ids:
        # obj.query returns a list, but should only have one element because
        # ids are unique.
        remove = obj.query.filter_by(id=remove_id)[0]
        db.session.delete(remove)

    db.session.commit()

    return redirect('display/'+category)


"""
HELPERS
"""


@login_manager.unauthorized_handler
def unauthorized():
    flash('You are not authorized to view this page, please login.')
    return redirect('/login')


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


@google.tokengetter
def get_access_token():
    return session.get('access_token')


def build_accordion(objects, accordion_id, type, extra=None):
    inner_t = app.jinja_env.get_template('accordion_inner.html')
    outer_t = app.jinja_env.get_template('accordion.html')

    inner = ""

    for obj in objects:
        inner += inner_t.render(accordion_id=accordion_id,
                                inner_id=obj.shortname,
                                type=type,
                                link=obj.name,
                                extra=None if not extra else extra % obj.id)

    return outer_t.render(accordion_id=accordion_id,
                          dump=inner)


def get_obj_by_category(category):
    # Checking for case insensitive categories
    categories = {'districts': District, 'schools': School,
                  'sites': Site, 'courses': Course}

    return categories.get(category.lower())


def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()


def district_details(schools):
    """
    district_details adds up the number of teachers, users, and admins of all
    the district's school's sites.

    Args:
        schools (list): list of schools to total the users, teachers, and
         admins.

    Returns:
        dict. The total admins, teachers, and users of the schools
    """

    admin_count = 0
    teacher_count = 0
    user_count = 0

    for school in schools:
        sites = Site.query.filter_by(school_id=school.id).all()
        for site in sites:
            details = SiteDetail.query.filter_by(site_id=site.id) \
                                      .order_by(SiteDetail
                                                .timemodified
                                                .desc()) \
                                      .first()
            if details:
                admin_count += details.adminusers
                teacher_count += details.teachers
                user_count += details.totalusers

    return {'admins': admin_count,
            'teachers': teacher_count,
            'users': user_count}

@app.route("/1/sites/<baseurl>/moodle")
def get_moodle_sites(baseurl):
    school_id = Site.query.filter_by(baseurl=baseurl).first().school_id
    moodle_sites = Site.query.filter_by(school_id=school_id).all()
    data = [{'id': site.id, 'name': site.name} for site in moodle_sites]
    return jsonify(content=data)
