from collections import defaultdict
import csv
import re
import sys

from flask import current_app, g
from flask.ext.script import Manager
import nose

from orvsd_central import attach_blueprints, create_app
from orvsd_central.database import (create_db_session, create_admin_account,
                                    init_db)


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
def gather_tokens():
    """
    For all sites added to ORVSD_Central's database and all services listed
    in the MOODLE_SERVICES config option, gather will gather all tokens for
    each service of every site
    """

    with current_app.app_context():
        from ovrsd_central.models import Site
        from orvsd_central.util import gather_tokens

        g.db_session = create_db_session()
        gather_tokens(Site.query.all())


@manager.option('-d', "--data", help="CSV to import of Districts and Schools")
def import_data(data):
    """
    CSV Format
    District State ID, District, School State ID, School, County
    """

    # schools are a list of values for the discricts (keys)
    district_schools = defaultdict(list)
    dist_state_ids = dict()

    with open(data, 'r') as csvfile:
        schools = csv.reader(csvfile)
        for row in schools:
            dist_state_ids[row[1]] = row[0]
            district_schools[row[1]].append(row[2:])

    with current_app.app_context():
        # Create a db session
        g.db_session = create_db_session()
        from orvsd_central.models import District, School

        # Only words, no symbols
        pattern = re.compile('[\W_]+')

        # For all the districts
        for key in district_schools.keys():
            # Search for the district or create it if it doesn't exist
            district = g.db_session.query(District).filter(
                District.name == key
            ).first()

            if not district:
                district = District(
                    state_id=dist_state_ids[key],
                    name=key,
                    shortname=pattern.sub('', key)
                )
                g.db_session.add(district)
                g.db_session.commit()

            # For the schools in the district, see if it exists,
            # else create it
            for school_row in district_schools[key]:
                school = g.db_session.query(School).filter(
                    School.name == school_row[1]
                ).first()

                if not school:
                    s = School(
                        district_id=district.id,
                        state_id=school_row[0],
                        name=school_row[1],
                        shortname=pattern.sub('', school_row[1]),
                        county=school_row[2]
                    )
                    g.db_session.add(s)

            # Commit the schools to the db
            g.db_session.commit()

    print "Data imported"


@manager.command
def create_admin(silent=False):
    """
    Create an admin account

    -s/--silent: flag to silence user input and instead look for ENVVARs for
    admin credentials
    """

    with current_app.app_context():
        g.db_session = create_db_session()
        create_admin_account(silent)


@manager.command
def initdb():
    """
    Sets up the schema for a database that already exists (MySQL, Postgres) or
    creates the database (SQLite3) outright.
    """

    with current_app.app_context():
        g.db_session = create_db_session()
        init_db()


@manager.option('-n', '--nosetest', help="Specific tests for nose to run")
def run_tests(nosetest):
    """
    Run Tests using nose
    """
    args = [sys.argv[0]] + nosetest if nosetest else [sys.argv[0]]

    with current_app.app_context():
        nose.main(argv=args)

if __name__ == '__main__':
    manager.run()
