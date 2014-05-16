from flask import current_app, g
from flask.ext.script import Manager

from orvsd_central import attach_blueprints, create_app
from orvsd_central.database import create_db_session, init_db


def setup_app(config=None):
    """
    Creates an instance of our application.

    We needed to create the app in this way so we could set different
    configurations within the same app. (hint: not using the same database
    when testing)
    """
    app = create_app(config) if config else create_app()
    with app.app_context():
        g.db_session = create_db_session()
        attach_blueprints()
        return app

# Setup our manager
manager = Manager(setup_app)
manager.add_option('-c', '--config', dest='config')


@manager.command
def gather():
    """
    Runs the gather_siteinfo script to generate SiteDetails.
    """
    with current_app.app_context():
        from orvsd_central.util import gather_siteinfo
        g.db_session = create_db_session()
        gather_siteinfo()


@manager.command
def initdb():
    """
    Sets up the schema for a database that already exists (MySQL, Postgres) or
    creates the database (SQLite3) outright.
    * This also includes an option to create a new user, but that won't work
      on an in-memory database.
    """
    with current_app.app_context():
        g.db_session = create_db_session()
        init_db()

if __name__ == '__main__':
    manager.run()
