from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for)
from flask.ext.login import (current_user, login_required,
                             login_user, logout_user)
import requests
from requests.exceptions import HTTPError

from sqlalchemy.exc import IntegrityError

from orvsd_central import constants
from orvsd_central.forms import AddUser, LoginForm
from orvsd_central.models import User
from orvsd_central.util import (google, is_valid_email,
                                login_manager, requires_role)


mod = Blueprint('general', __name__)


@mod.route('/')
def root():
    """
    Returns the report page if a user is logged in, otherwise the login page.
    """
    if not current_user.is_anonymous():
        return redirect(url_for('report.index'))
    return redirect(url_for('general.login'))


@mod.route("/register", methods=['GET', 'POST'])
@requires_role('admin')
@login_required
def register():
    """
    Returns a registration template for creating new users.
    """

    # user=current_user
    form = AddUser()
    message = ""

    if request.method == "POST":
        if not form.user.data:
            message = "Please enter a username.\n"
        elif not is_valid_email(form.email.data):
            message = "This does not look like an E-mail. Please try again.\n"
        elif not form.password.data:
            message = "Please enter a password.\n"
        elif form.password.data != form.confirm_pass.data:
            message = "The passwords provided did not match!\n"
        else:
            # Add user to db
            try:
                user = User(
                    name=form.user.data,
                    email=form.email.data,
                    password=form.password.data,
                    role=constants.USER_PERMS.get(form.role.data, 1)
                )
                g.db_session.add(user)
                g.db_session.commit()

                message = form.user.data + " has been added successfully!\n"
            except IntegrityError:
                g.db_session.rollback()
                if User.query.filter_by(email=form.email.data).first():
                    message = "Email is already in use.\n"
                else:  # assume error was duplicate username since not email
                    message = "Username is already in use.\n"

    return render_template('add_user.html', form=form,
                           message=message, user=current_user)


@mod.route("/login", methods=['GET', 'POST'])
def login():
    """
    Handles login.
    * login_user is a function from Flask-Login for handling authentication,
      sessions, and more for logins.
    """
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(name=form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.", category='info')
            return redirect(url_for("report.index"))
        else:
            flash(
                "Username or Password was not recognized. Please try again.",
                category='error'
            )

    # current_user should be anonymous at this point which does not have a role
    # thus requiring some value for user.role or jinja2 complains with an
    # undifinedvalue error
    current_user.role = -1

    return render_template("login.html", form=form, user=current_user)


@mod.route("/google_login")
def google_login():
    """
    Handles login through google oauth instead of through our system.
    """
    access_token = session.get('access_token')
    if access_token is None:
        callback = url_for('general.authorized', _external=True,
                           _scheme='https')
        return google.authorize(callback=callback)
    else:
        access_token = access_token
        payload = {'Authorization': 'OAuth ' + access_token}
        req = requests.get('https://www.googleapis.com/oauth2/v1/userinfo',
                           headers=payload)
        try:
            req.raise_for_status()
        except HTTPError:
            if req.status_code == 401:
                session.pop('access_token', None)
                flash(
                    "Incorrect google Username or Password, please try again",
                    category='error'
                )
                return redirect(url_for('general.login'))
            return req.raw.read()
        obj = req.json()
        email = obj['email']
        user = User.query.filter_by(email=email).first()
        # pop access token so it isn't sitting around in our
        # session any longer than nescessary
        session.pop('access_token', None)
        if user is not None:
            login_user(user)
            return redirect(url_for('report.index'))
        else:
            flash(
                "That google account does not have access.",
                category='error'
            )
            return redirect(url_for('general.login'))


@mod.route("/logout")
@login_required
def logout():
    """
    Logs out a user.
    """
    logout_user()
    return redirect(url_for("general.login"))


@mod.route(current_app.config['REDIRECT_URI'])
@google.authorized_handler
def authorized(resp):
    """
    Checks an access token set by google for authorization to log in.
    """
    access_token = resp['access_token']
    session['access_token'] = access_token
    return redirect(url_for('general.google_login'))


@google.tokengetter
def get_access_token():
    """
    Gets the session's access token.
    """
    return session.get('access_token')


@login_manager.unauthorized_handler
def unauthorized():
    """
    Handler for unauthorized users. Returns the user to a login page.
    """
    flash(
        "You are not authorized to view this page, please login.",
        category='error'
    )
    return redirect(url_for('general.login'))
