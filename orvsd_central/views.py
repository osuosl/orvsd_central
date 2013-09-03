from flask import (request, render_template, flash, g, session, redirect,
                   url_for, abort, jsonify)
from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from werkzeug import check_password_hash, generate_password_hash
from orvsd_central import db, app, login_manager, google, celery
from forms import LoginForm, AddUser, InstallCourse
from models import (District, School, Site, SiteDetail,
                    Course, CourseDetail, User)
from sqlalchemy import func, and_
from sqlalchemy.sql.expression import desc
from models import (District, School, Site, SiteDetail,
                    Course, CourseDetail, User)
import celery
import json
import re
import subprocess
import StringIO
import requests


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
INSTALL
"""

@app.route('/get_site_by/<int:site_id>', methods=['GET'])
def site_by_id(site_id):
    address = Site.query.filter_by(id=site_id).first().baseurl
    return jsonify(address=address)

@app.route('/install/course', methods=['GET', 'POST'])
def install_course():
    """
    Displays a form for the admin user to pick courses to install on a site

    Returns:
        Rendered template
    """


    if request.method == 'GET':
        form = InstallCourse()

        # Query all moodle 2.2 courses
        courses = db.session.query(CourseDetail).filter(
                                        CourseDetail.moodle_version.like('2.5%')) \
                                    .all()

        # Query all moodle sites
        sites = Site.query.filter_by(sitetype='moodle').all()
        moodle_22_sites = []

        # For all sites query the SiteDetail to see if it's a moodle 2.2 site
        for site in sites:
            details = db.session.query(SiteDetail).filter(and_(
                SiteDetail.site_id == site.id,
                SiteDetail.siterelease.like('2.2%'))
            ).order_by(SiteDetail.timemodified.desc()).first()

            if details is not None:
                moodle_22_sites.append(site)

        # Generate the list of choices for the template
        courses_info = []
        sites_info = []

        # Create the courses list
        for course in courses:
            courses_info.append(
                (course.course_id, "%s - v%s"
                % (course.course.name, course.version)))

        # Create the sites list
        for site in moodle_22_sites:
            sites_info.append((site.id, site.name))

        form.course.choices = sorted(courses_info, key=lambda x: x[1])
        form.site.choices = sorted(sites_info, key=lambda x: x[1])

        return render_template('install_course.html',
                               form=form, user=current_user)

    elif request.method == 'POST':
        # Course installation results
        output = ''

        # An array of unicode strings will be passed, they need to be integers
        # for the query
        selected_courses = [int(cid) for cid in request.form.getlist('course')]

         # The CourseDetail objects needed to generate the url
        courses = CourseDetail.query.filter(CourseDetail
                                            .course_id.in_(selected_courses))\
                                        .all()


        site_ids = [site_id for site_id in request.form.getlist('site')]
        site_urls = [Site.query.filter_by(id=site_id).first().baseurl for site_id in site_ids]

        for site_url in site_urls:
            # The site to install the courses
            site = "http://%s/webservice/rest/server.php?wstoken=%s&wsfunction=%s" % (
                   site_url,
                   app.config['INSTALL_COURSE_WS_TOKEN'],
                   app.config['INSTALL_COURSE_WS_FUNCTION'])
            site = str(site.encode('utf-8'))

            # Loop through the courses, generate the command to be run, run it, and
            # append the ouput to output
            #
            # Currently this will break as our db is not setup correctly yet
            for course in courses:
                #Courses are detached from session for being inactive for too long.
                course.course.name
                install_course_to_site.delay(course, site)

            output += str(len(courses)) + " course install(s) for " + site_url + " started.\n"

        return render_template('install_course_output.html',
                                output=output,
                                user=current_user)

@celery.task(name='tasks.install_course')
def install_course_to_site(course, site):
    # To get the file path we need the text input, the lowercase of
    # source, and the filename
    fp = app.config['INSTALL_COURSE_FILE_PATH']
    fp += course.course.source.lower() + '/'

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

    resp = requests.post(site, data=data)

    # Unfortunately the response object to turned into unicode
    # when returned by the celery job, so we must send the
    # data we need, instead of the whole object.
    return resp.text
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
UPDATE
"""


@app.route("/<category>/update")
@login_required
def update(category):
    obj = get_obj_by_category(category)
    identifier = get_obj_identifier(category)
    if obj:
        if 'details' in category:
            category = category.split("details")[0] + " Details"
        category = category[0].upper() + category[1:]

        objects = obj.query.order_by(identifier).all()
        if objects:
            return render_template("update.html", objects=objects,
                                    identifier=identifier, category=category,
                                    user=current_user)

    abort(404)


@app.route("/<category>/object/add", methods=["POST"])
def add_object(category):
    obj = get_obj_by_category(category)
    if obj:
        inputs = {}
        # Here we update our dict with new values
        # A one liner is too messy :(
        for column in obj.__table__.columns:
            if column.name is not 'id':
                inputs.update({column.name: string_to_type(
                                request.form.get(column.name))})

        new_obj = obj(**inputs)
        db.session.add(new_obj)
        db.session.commit()
        return jsonify({'id': new_obj.id,
                'message': "Object added successfully!"})

    abort(404)


@app.route("/<category>/<id>", methods=["GET"])
def get_object(category, id):
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=id).first()
        if modified_obj:
            return jsonify(modified_obj.serialize())

    abort(404)


@app.route("/<category>/<id>/update", methods=["POST"])
def update_object(category, id):
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=request.form.get("id")).first()
        if modified_obj:
            inputs = {}
            # Here we update our dict with new
            [inputs.update({key: string_to_type(request.form.get(key))})
                        for key in modified_obj.serialize().keys()]

            db.session.query(obj).filter_by(
                    id=request.form.get("id")) \
                .update(inputs)

            db.session.commit()
            return "Object updated sucessfully!"

    abort(404)


@app.route("/<category>/<id>/delete", methods=["POST"])
def delete_object(category, id):
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=request.form.get("id")).first()
        if modified_obj:
            db.session.delete(modified_obj)
            db.session.commit()
            return "Object deleted successful!"

    abort(404)


@app.route("/<category>/keys")
def get_keys(category):
    obj = get_obj_by_category(category)
    if obj:
        cols = dict((column.name, '') for column in
                    obj.__table__.columns)
        return jsonify(cols)


def string_to_type(string):
    # Have to watch out for the format of true/false/null
    # with javascript strings.
    if string == "true":
        return True
    elif string == "false":
        return False
    elif string == "null":
        return None
    try:
        return float(string)
    except ValueError:
        if string.isdigit():
            return int(string)
    return string

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
                  'sites': Site, 'courses': Course, 'users': User,
                  'coursedetails': CourseDetail, 'sitedetails': SiteDetail}

    return categories.get(category.lower())

def get_obj_identifier(category):
    categories = {'districts': 'name', 'schools': 'name',
                  'sites': 'name', 'courses': 'name', 'users': 'name',
                  'coursedetails': 'filename', 'sitedetails': 'site_id'}

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

#ORVSD Central API

@app.route("/1/sites/<baseurl>/moodle")
def get_moodle_sites(baseurl):
    school_id = Site.query.filter_by(baseurl=baseurl).first().school_id
    moodle_sites = Site.query.filter_by(school_id=school_id).all()
    data = [{'id': site.id, 'name': site.name} for site in moodle_sites]
    return jsonify(content=data)


@app.route("/1/sites/<baseurl>")
def get_site_by_url(baseurl):
    site = Site.query.filter_by(baseurl=baseurl).first()
    if site:
        site_details = SiteDetail.query.filter_by(site_id=site.id) \
                                       .order_by(SiteDetail
                                                 .timemodified
                                                 .desc()) \
                                       .first()

        site_info = dict(site.serialize().items() + \
                    site_details.serialize().items())

        return jsonify(content=site_info)
    return jsonify(content={'error': 'Site not found'})


@app.route("/1/get_count/<id>")
def get_id_count(id):
    return str(get_count('teachers', District.query.filter_by(id=id).first()))

@app.route("/test")
def get_dup_schools():
    schools = School.query.all()
    duplicate_districts = []
    districts = {}
    for school in schools:
        if districts.get(school.district_id):
            districts[school.district_id] += 1
        else:
            districts.update({school.district_id: 1})

    for key in districts:
        if districts.get(key) > 1:
            duplicate_districts.append(key)

    site_districts = [District.query.filter_by(id=id).first() for id in duplicate_districts]
    import datetime
    start = datetime.datetime.now()
    site_districts = District.query.all()
    fields = ['admins', 'teachers', 'totalusers']
    district_info = [[district.name, district.id, len(district.schools), get_count(fields, district, {})] for district in site_districts]
    print "Time taken: "+str(datetime.datetime.now()-start)
    return render_template("test.html", data=district_info, fields=fields)


# Must send in an object! No 'districts', 'courses', etc.
def get_count(fields, base_obj, data):
    association_objs, obj_present = get_association_obj(base_obj)
    if association_objs:
        if hasattr(association_objs, '__iter__'):
            if len(association_objs) > 1:
                for obj in association_objs:
                    get_count(fields, obj, data)
            else:
                get_count(fields, association_objs[0], data)
        else:
            get_count(fields, association_objs, data)
    elif not obj_present: # Base Case
        serialized = base_obj.serialize()
        for field in fields:
            if serialized.get(field) is not None:
                if not data.get(field):
                    data[field] = 0
                data[field] += int(serialized.get(field))
    return data

# Input:  Object instance, that is a subclass of Model
# Output: 1. Next object in the association graph
#         2. Continue looking for associations?
def get_association_obj(obj):
    if isinstance(obj, District):
        return (obj.schools, True)
    elif isinstance(obj, School):
        return (obj.sites, True)
    elif isinstance(obj, Site):
        details = sorted(obj.site_details, key=lambda x:
                             x.timemodified)
        if details:
            return (details[-1], False)
    return (None, False)

@app.route("/1/<category>/<id>/associated_objs", methods=["GET", "POST"])
def get_associated_objs(category, id):
    obj_type = get_obj_by_category(category)
    if obj_type:
        parent_obj = obj_type.query.filter_by(id=id).first()
        associated_objs, obj_present = get_association_obj(obj)
        if obj_present:
            children_objs = [(obj.id, obj.name) for obj in associated_objs]
            return jsonify(content=children_objs)

    return jsonify({'error': 'No more associated objs'})
