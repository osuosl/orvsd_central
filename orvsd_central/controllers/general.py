from flask import Blueprint, flash, render_template, redirect, session, url_for
from flask.ext.login import (current_user, login_required,
                             login_user, logout_user)
import requests

from orvsd_central import app, db, google
from orvsd_central.forms import AddUser, LoginForm
from orvsd_central.models import User
from orvsd_central.util import requires_role

mod = Blueprint('general', __name__)


@mod.route('/')
@login_required
def root():
    if not current_user.is_anonymous():
        return redirect(url_for('report'))
    return redirect(url_for('general.login'))


@mod.route("/register", methods=['GET', 'POST'])
@requires_role('admin')
@login_required
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
                                password=form.password.data,
                                role=constants.USER_PERMS
                                              .get(form.role.data, 1)))
            db.session.commit()
            message = form.user.data + " has been added successfully!\n"

    return render_template('add_user.html', form=form,
                           message=message, user=current_user)


@mod.route("/login", methods=['GET', 'POST'])
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


@mod.route("/google_login")
def google_login():
    access_token = session.get('access_token')
    if access_token is None:
        callback = url_for('general.authorized', _external=True)
        return google.authorize(callback=callback)
    else:
        access_token = access_token
        payload = {'Authorization': 'OAuth ' + access_token}
        req = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',
                           headers=payload)
        try:
            req.raise_for_status()
        except HTTPError, e:
            if req.status_code == 401:
                session.pop('access_token', None)
                flash('There was a problem with your Google \
                      login information.  Please try again.')
                return redirect(url_for('general.login'))
            return req.raw.read()
        obj = req.json()
        email = obj['email']
        user = User.query.filter_by(email=email).first()
        #pop access token so it isn't sitting around in our
        #session any longer than nescessary
        session.pop('access_token', None)
        if user is not None:
            login_user(user)
            return redirect(url_for('report'))
        else:
            flash("That google account does not have access.")
            return redirect(url_for('general.login'))


@mod.route(app.config['REDIRECT_URI'])
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token
    return redirect(url_for('general.google_login'))


@mod.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("general.login"))
