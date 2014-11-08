import os

from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import IntegrityError

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
    command 'create_admin'
    Create an admin account. This con be done via raw input from the user or
    through config variables

    config: Bool - use config vars
    """
    from orvsd_central.util import (prompt_valid_email,
                                    prompt_matching_passwords)

    if not silent:
        # get the number of admins
        admin_role = USER_PERMS.get('admin')
        admin_count = User.query.filter_by(role=admin_role).count()
        print("There are currently %d admin accounts." % admin_count)

        ans = raw_input("Would you like to create an admin account? (Y/N) ")
        if not ans.lower().startswith("y"):
            return

        # Proceed to making the admin user.
        admin_created = False
        while not admin_created:
            username = raw_input("Username: ")
            while not username:
                print("Please input a username")
                username = raw_input("Username: ")

            email = prompt_valid_email()
            password = prompt_matching_passwords()

            # Get admin role.
            admin = User(
                name=username,
                email=email,
                password=password,
                role=admin_role
            )

            try:
                g.db_session.add(admin)
                g.db_session.commit()
                admin_created = True
            except IntegrityError:
                g.db_session.rollback()
                if User.query.filter_by(email=email).first():
                    print("Email is already in use.\n")
                else:  # assume error was duplicate username since not email
                    print("Username is already in use.\n")

    else:  # silent
        username = os.getenv('CENTRAL_ADMIN_USERNAME', 'admin')
        password = os.getenv('CENTRAL_ADMIN_PASSWORD', 'admin')
        email = os.getenv('CENTRAL_ADMIN_EMAIL', 'example@example.com')

        # Get admin role.
        admin_role = USER_PERMS.get('admin')
        admin = User(
            name=username,
            email=email,
            password=password,
            role=admin_role
        )

        try:
            g.db_session.add(admin)
            g.db_session.commit()
        except IntegrityError:
            g.db_session.rollback()

    print "Administrator account created!"


def init_db():
    engine = g.db_session.get_bind()
    Model.metadata.create_all(bind=engine)
