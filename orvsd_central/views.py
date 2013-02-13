from flask import request, render_template, flash, g, session, redirect, url_for
from flask.ext.login import login_required, login_user, logout_user, current_user
from werkzeug import check_password_hash, generate_password_hash
from orvsd_central import db, app, login_manager
from forms import LoginForm, AddDistrict, AddSchool, AddUser, AddCourse
from models import District, School, Site, SiteDetail, Course, CourseDetail, User
import re

def no_perms():
    return "You do not have permission to be here!"

@app.route("/")
#@login_required
def main_page():
    return redirect('/report')

@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()

@app.route("/login", methods=['GET', 'POST'])
def login():
    form=LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(name=form.name.data).first()
        print check_password_hash
        if user and user.password == form.password.data:
            login_user(user)
            flash("Logged in successfully.")
            return redirect("/add_school")

    return render_template("login.html", form=form)

def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session::
            return User.query.filter_by(id=session["user_id"]).first()
    return None

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")

@app.route("/add_district", methods=['GET', 'POST'])
def add_district():
    form = AddDistrict()
    user = get_user()
    if request.method == "POST":
        #Add district to db.
        db.session.add(District(form.name.data, form.shortname.data,
                        form.base_path.data))
        db.session.commit()

    return render_template('add_district.html', form=form, user=user)

#@login_required
@app.route("/add_school", methods=['GET', 'POST'])
def add_school():
    form = AddSchool()
    user = get_user()
    msg = ""

    if request.method == "POST":
        #The district_id is supposed to be an integer
        district = District.query.filter_by(id=int(form.district_id.data)).all()
        if len(district) == 1:
            #Add School to db
            db.session.add(School(int(form.district_id.data),
                        form.name.data, form.shortname.data,
                        form.domain.data. form.license.data))
            db.session.commit()
        else:
            msg= "A district with that id doesn't exist!"
    return render_template('add_school.html', form=form,
                        msg=msg, user=user)

@app.route("/add_course", methods=['GET', 'POST'])
def add_course():
    form = AddCourse()
    user = get_user()
    msg = ""
    if request.method == "POST":
        db.session.add(Course(int(form.serial.data), form.name.data,
                            form.shortname.data, form.license.data,
                            form.category.data))
        db.session.commit()
        msg = "Course: "+form.name.data+"added successfully!"

    return render_template('add_course.html', form=form, msg=msg, user=user)


@app.route('/me')
@login_required
def home():
    """
    Loads a users home information page
    """
    return render_template('users/templates/profile.html', user=current_user) #not sure current_user works this way, write test

"""
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm(csrf_enabled=False)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Successful Login!")
            return redirect("/users/me/")
    return render_template("login.html", form=form)
"""
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route("/report", methods=['GET', 'POST'])
#@login_required
def report():
    user = get_user()

    all_districts = District.query.order_by("name").all()
    all_schools = School.query.order_by("name").all()
    all_courses = Course.query.order_by("name").all()
    all_sites = Site.query.order_by("sitename").all()

    districts = all_districts
    schools = all_schools
    courses = all_courses

    # Once filters have been applied
    if request.method== "POST":
        form = request.form
        # Check to see if the user wants to see district info
        if request.form['all_districts'] != "None":
        # Getting district related information
            if request.form['all_districts'] != "All":
                districts = District.query.filter_by(name=request.form['filter_districts'])
            for district in districts:
                district.schools = School.query.filter_by(disctrict_id=district.id).order_by("name").all()
                for school in district.schools:
                    school.sites = Site.query.filter_by(school_id=school.id).order_by("name").all()
                    for site in sites:
                        related_courses = session.execute("select course_id where site_id="+site.id+" from sites_courses")
                        site.courses = []
                        site.courses.append(Course.query.get(course))

            districts = None
            # Check to see if the user wanted school information
            if request.form['all_schools'] != "None":
                if request.form['all_schools'] != "All":
                    schools = School.query.filter_by(name=request.form['filter_schools']).order_by("name").all()
                for school in schools:
                    school.sites = Site.query.filter_by(school_id=school.id).order_by("name").all()
                    for site in sites:
                        related_courses = session.execute("select course_id where site_id="+site.id+" from sites_courses")
                        for course in related_courses:
                            # course is the primary key which is used to relate a site's course to a specific course.
                            site.courses.append(Course.query.get(course))
                        for course in site.courses:
                            # Parse information from SiteDetails
                            continue

            else:
                schools = None
                # Check to see if the user wanted course information
                if request.form['all_courses'] != "None":
                    if request.form['all_courses'] != "All":
                        courses = Course.query.filter_by(name=request.form['filter_courses']).order_by("name").all()
                    for course in courses:
                        #Calculate num of users in total
                        continue
                else:
                    return "Error: No filter provided!!"
    else:
        districts = all_districts
        schools = all_schools
        courses = all_courses

    return render_template("report.html", all_districts=all_districts,
                                          all_schools=all_schools,
                                          all_courses=all_courses,
                                          all_sites=all_sites, user=user)

@app.route("/add_user", methods=['GET', 'POST'])
#@login_required
def register():
    user = get_user()
    form = AddUser()
    message = ""

    if request.method == "POST":
        if form.password.data != form.confirm_pass.data:
            message="The passwords provided did not match!\n"
        elif not re.match('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$', form.email.data):
            message="Invalid email address!\n"
        else:
            #Add user to db
            db.session.add(User(name=form.user.data,
                email = form.email.data, password=form.password.data))

            message = form.user.data+" has been added successfully!\n"

    return render_template('add_user.html', form=form, message=message, user=user)

@app.route("/display/<category>")
def remove(category):
    user = get_user()
    obj = get_obj_by_category(category)
    objects = obj.query.all()
    if objects:
        # fancy way to get the properties of an object
        properties = objects[0].get_properties()
        return render_template('removal.html', category=category, objects=objects, properties=properties, user=user)


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

def get_obj_by_category(category):
    if category == "Districts":
        return District
    elif category == "Schools":
        return School
    elif category == "Sites":
        return Site
    elif category == "Courses":
        return Course
    else:
        raise Exception('Invalid category: '+category)



