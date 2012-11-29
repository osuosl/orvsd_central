from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
from werkzeug import check_password_hash, generate_password_hash
from flask.ext.login import login_required, login_user, logout_user, current_user

from orvsd_central import db
from forms import LoginForm #add regester form when needed
from models import User

userblp = Blueprint('users', __name__, url_prefix="/users")

@userblp.route('/me/')
@login_required
def home():
    """
    Loads a users home information page
    """
    return render_template('users/templates/profile.html', user=current_user) #not sure current_user works this way, write test

@userblp.route("/login/", methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Successful Login!")
            return redirect("/users/me/")
    return render_template("login.html", form=form)

@userblp.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect('/login/')


