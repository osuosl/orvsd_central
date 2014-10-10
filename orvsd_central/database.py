import os
import sys

from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import IntegrityError

from orvsd_central.util_validation import (prompt_valid_email,
                                           prompt_matching_passwords)

from orvsd_central.constants import USER_PERMS
from orvsd_central.models import Model, User

def create_db_session():
    # Get the db address from the current app
    _db_address = current_app.config['SQLALCHEMY_DATABASE_URI']

    engine = create_engine(_db_address, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Model.query = db_session.query_property()
    return db_session


def create_admin_account(silent):
    """
    Create an admin account. This con be done via raw input from the user or
    through config variables

    config: Bool - use config vars
    """

    # make sure the role is defined
    admin_role = USER_PERMS.get('admin')
    if not admin_role:
        sys.exit('admin key is needed in constants.USER_PERMS')

    if not silent:
        # get the number of admins
        admin_count = User.query.filter_by(role=admin_role).count()
        print("There are currently %d admin accounts." % admin_count)

        ans = raw_input("Would you like to create an admin account? (Y/N) ")
        if not ans.lower().startswith("y"):
            return

        # Proceed to making the admin user.
        username = raw_input("Username: ")
        while not username:
            print("Please input a username")
            username = raw_input("Username: ")

        email = prompt_valid_email()
        password = prompt_matching_passwords()
    else:
        username = os.getenv('CENTRAL_ADMIN_USERNAME', 'admin')
        password = os.getenv('CENTRAL_ADMIN_PASSWORD', 'admin')
        email = os.getenv('CENTRAL_ADMIN_EMAIL', 'example@example.com')

    # Get admin role.
    admin_role = USER_PERMS.get('admin')
    admin = User (
        name=username,
        email=email,
        password=password,
        role=admin_role
    )

    try:
        g.db_session.add(admin)
        g.db_session.commit()
    except IntegrityError:
        if User.query.filter_by(email=email).first():
            print("Email is already in use.\n")
        else: # assume error was duplicate username since not email
            print("Username is already in use.\n")
        exit(-1)

    print "Administrator account created!"


def init_db():
    engine = g.db_session.get_bind()
    from orvsd_central import models
    Model.metadata.create_all(bind=engine)
