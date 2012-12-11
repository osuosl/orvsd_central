from flask import request, render_template, flash, g, session, redirect, url_for
from flask.ext.login import login_required, login_user, logout_user, current_user
from werkzeug import check_password_hash, generate_password_hash
from orvsd_central import db
from forms import LoginForm #add register form when needed

from orvsd_central import db, lm
from forms import LoginForm #add regester form when needed
>>>>>>> e49bbdc869f247400ca359495379e40c94bc4ce5
from models import User
import re

@app.route("/")
@login_required
def main_page():
    return redirect('/report')

@app.route('/me')
@login_required
def home():
    """
    Loads a users home information page
    """
    return render_template('users/templates/profile.html', user=current_user) #not sure current_user works this way, write test

@app.route("/login", methods=['GET', 'POST'])
@login_required
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
@login_required
def report():
    
    districts, schools, districts = None

    if request.method== "POST":
        form = request.form
        
    else:# The initial page
        # Get list of all districts
        # Get list of all schools
        # Get list of all courses

    return render_template("reports.html", 

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

