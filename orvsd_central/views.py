from flask import request, render_template, flash, g, session, redirect, url_for
from flask.ext.login import login_required, login_user, logout_user, current_user
from werkzeug import check_password_hash, generate_password_hash
from orvsd_central import db, lm, app
from forms import LoginForm, AddDistrict, AddSchool
from models import District, School, Site, SiteDetail, Course, CourseDetail
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re

@app.route("/")
#@login_required
def main_page():
    return redirect('/report')

@app.route("/add_district", methods=['GET', 'POST'])
def add_district():
    form = AddDistrict()
    if request.method == "POST":
        #Add district to db.
        db.session.add(District(form.name.data, form.shortname.data,
                        form.base_path.data))
        db.session.commit()

    return render_template('add_district.html', form=form)

@app.route("/add_school", methods=['GET', 'POST'])
def add_school():
    form = AddSchool()
    error_msg = ""

    if request.method == "POST":
        #The district_id is supposed to be an integer
        try:
            district = District.query.filter_by(id=int(form.name.data)).all()
            if len(district) == 1:
                #Add School to db
                db.session.add(School(int(form.district_id.data),
                        form.name.data, form.shortname.data,
                        form.domain.data. form.license.data))
                db.session.commit()
            else:
                error_msg= "A district with that id doesn't exist!"
        except:
            error_msg= "The entered district_id was not an integer!"
    return render_template('add_school.html', form=form,
                        error_msg=error_msg)


@app.route('/me')
@login_required
def home():
    """
    Loads a users home information page
    """
    return render_template('users/templates/profile.html', user=current_user) #not sure current_user works this way, write test

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Successful Login!")
            return redirect("/users/me/")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route("/report", methods=['GET', 'POST'])
#@login_required
def report():

    all_districts = District.query.all()
    all_schools = School.query.all()
    all_courses = Course.query.order_by("name").all()

    """
    for district in all_districts:
        district.schools = School.query.filter_by(district=district.name).all()

    for school in all_schools:
        school.sites = Site.query.filter_by(school=school.name).all()
        # Do some parsing on sites_courses
        for site in school.sites:
            #Look up sites_courses table and relate the sites id and
            #courses on that site
            pass
        pass
    """
    # Once filters have been applied
    if request.method== "POST":
        form = request.form

        if request.form['filter_districts'] == "All":
            districts = all_districts
        else:
            districts = District.query.filter_by(name=request.form['filter_districts'])
            pass
        if request.form['filter_schools'] == "All":
            schools = all_schools
        else:
            #schools = query for filtered_schools
            schools = School.query.filter_by(name=request.form['filter_schools'])
            pass
        if request.form['filter_courses'] == "All":
            courses = all_courses
        else:
            #courses = query for filtered_courses
            courses = Course.query.filter_by(name=request.form['filter_courses'])
            pass

    else:
        districts = all_districts
        schools = all_schools
        courses = all_courses
        pass

    return render_template("report.html", all_districts=all_districts,
                                          all_schools=all_schools,
                                          all_courses=all_courses,)

@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    user = True
    message = ""

    if request.method == "POST":
        print request.form
        # Can not test until the inital migration is pushed.
        #if User.query.filter_by(username=request.form['username']).first ():
        #    message="This username already exists!\n"
        if request.form['password'] is not request.form['confirm_password']:
            message="The passwords provided did not match!\n"
        elif not re.match('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$', request.form['email']):
            message="Invalid email address!\n"
        else:
            #Add user to db
            message=request.form['username']+" has been added successfully!\n"

    #Check for a good username
    return render_template('register.html', user=user, message=message)

