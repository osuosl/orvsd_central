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

def init_db():
    engine = g.db_session.get_bind()
    from orvsd_central import models
    Model.metadata.create_all(bind=engine)

    # Create an admin account.
    ans = raw_input("There are currently no admin accounts, would you like to "
                    "create one? (Y/N) ")
    if not ans.lower().startswith("y"):
        return
    username = raw_input("Username: ")
    email = raw_input("Email: ")
    matching = False
    while not matching:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm Password: ")
        matching = password == confirm
        if not matching:
            print "Passwords do not match. Please try again."

    # Get admin role.
    admin_role = USER_PERMS.get('admin')
    admin = models.User(name=username,
                        email=email,
                        password=password,
                        role=admin_role)

    g.db_session.add(admin)
    g.db_session.commit()

    print "Administrator account created!"
