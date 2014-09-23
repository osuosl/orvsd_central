import os

from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from orvsd_central.constants import USER_PERMS

import getpass

Model = declarative_base()


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

    if silent:
        # Create an admin account.
        ans = raw_input("There are currently no admin accounts, would you like to "
                        "create one? (Y/N) ")
        if not ans.lower().startswith("y"):
            return

        username = raw_input("Username: ")
        user_exists = User.query.filter_by(name=username).first()
        while user_exists:
            print "Username was already taken. Please try a different name."
            username = raw_input("Username: ")
            user_exists = User.query.filter_by(name=username).first()

        email = raw_input("Email: ")
        email_exists = User.query.filter_by(email=email).first()
        while email_exists:
            print "Email is in use for another user. Please try a different email."
            email = raw_input("Email: ")
            email_exists = User.query.filter_by(email=username).first()

        matching = False
        while not matching:
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm Password: ")
            matching = password == confirm
            if not matching:
                print "Passwords do not match. Please try again."
    else:
        username = os.getenv('CENTRAL_ADMIN_USERNAME', 'admin')
        password = os.getenv('CENTRAL_ADMIN_PASSWORD', 'admin')
        email = os.getenv('CENTRAL_ADMIN_EMAIL', 'example@example.com')

    # Get admin role.
    from orvsd_central.models import User

    user_exists = g.db_session.query(User).filter(User.name==username)
    email_exists = g.db_session.query(User).filter(User.email==email)

    if user_exists:
        print "Username already in use."
    elif email_exists:
        print "Email address already in use."
    else:
        admin_role = USER_PERMS.get('admin')
        admin = User(
            name=username,
            email=email,
            password=password,
            role=admin_role
        )

        g.db_session.add(admin)
        g.db_session.commit()

        print "Administrator account created!"

def init_db():
    engine = g.db_session.get_bind()
    from orvsd_central import models
    Model.metadata.create_all(bind=engine)
