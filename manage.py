from collections import defaultdict
import csv
import logging
import os
import re
import sys

from flask import current_app, g
from flask.ext.script import Manager
import nose
import requests

from orvsd_central import create_app
from orvsd_central.database import (create_db_session, create_admin_account,
                                    init_db)


def setup_app(config=None):
    return create_app(config) if config else create_app()


# Setup our manager
manager = Manager(setup_app)
manager.add_option('-c', '--config', dest='config')


@manager.command
def gather_siteinfo():
    """
    Gather SiteInfo

    This is a nice management wrapper to the util method that grabs moodle
    sitedata from the orvsd_siteinfo webservice plugin for all sites in
    orvsd_central's database
    """

    with current_app.app_context():
        from orvsd_central.models import Site
        from orvsd_central.util import gather_siteinfo
        g.db_session = create_db_session()

        for site in Site.query.all():
            gather_siteinfo(site)


@manager.command
def gather_tokens():
    """
    For all sites added to ORVSD_Central's database and all services listed
    in the MOODLE_SERVICES config option, gather will gather all tokens for
    each service of every site
    """

    with current_app.app_context():
        from orvsd_central.models import Site
        from orvsd_central.util import gather_tokens
        g.db_session = create_db_session()

        for site in Site.query.all():
            gather_tokens(site)


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
def setup_db():
    """
    Either initialize the database if none yet exists, or migrate as needed
    """

    from alembic.config import Config
    from alembic import command

    with current_app.app_context():
        # Alembic config used by migration or stamping
        alembic_cfg = Config(
            os.path.join(current_app.config["PROJECT_PATH"], "alembic.ini")
        )

        # Database connections
        g.db_session = create_db_session()
        con = g.db_session.connection()

        # Query list of existing tables
        tables = con.execute("show tables").fetchall()
        alembic_table = ('alembic_version',)
        if alembic_table in tables:
            # Latest version has been stamped or we have been upgrading
            logging.info("Database: Migrating")
            command.upgrade(alembic_cfg, "head")
        else:
            # The database needs to be initialized
            logging.info("Database: Initializing")
            init_db()
            command.stamp(alembic_cfg, "head")


@manager.option('-d', "--data", help="File to import of Sites")
def update_sites(data):
    """
    Expected Format:
    ./ashland/moodle22/languages.orvsd.org
    ./astoria/moodle22/astoria22.orvsd.org
    ./beaverton/moodle22/beaverton22.orvsd.org
    """

    with current_app.app_context():
        # Create a db session
        g.db_session = create_db_session()
        from orvsd_central.models import Site
        from orvsd_central.util import gather_siteinfo, gather_tokens

        # Used for finding a default nginx page.
        random_domain = 'http://randomdomain.oregonachieves.org'
        nginx_default = requests.get(random_domain).text
        is_not_default = lambda d: requests.get(d).text != nginx_default

        orvsd_sites = set(map(lambda x: x[0],
                            g.db_session.query(Site.baseurl).distinct()))
        filepaths = {}
        server_sites = set()
        with open(data, 'r') as f:
            prefix = '/var/www/'
            f = f.read().strip().replace('./', '')
            for line in f.split('\n'):
                line = line.strip()
                base_url = line.split('/')[-1]
                if is_not_default('http://' + base_url):
                    filepaths[base_url] = prefix + line + '/'
                    server_sites.add(base_url)
                else:
                    print 'Default nginx page for %s' % base_url

        if not server_sites:
            print 'No sites retrieved from input file. Was the format correct?'
            exit()

        # Retrieve sites in the server site list, but not on ORVSD
        sites_to_add = server_sites - orvsd_sites
        to_add = defaultdict(dict)
        for site in sites_to_add:
            subdomain = site.split('.')[0]
            name = ' '.join(map(lambda x: x.capitalize(), subdomain.split('_')))
            to_add[site] = {
                'school_id': None,
                'name': name,
                'sitetype': 'moodle',
                'baseurl': site,
                'basepath': filepaths[site],
                'machine': '',
                'moodle_tokens': ''
            }

        '''
        new_sites = []
        for site in to_add:
            new_site = Site(**site)
            new_sites.append(new_site)
            g.db_session.add(new_site)
        g.db_session.commit()

        not_in_server = orvsd_sites - server_sites
        # Delete sites that weren't on the server.
        to_delete = (g.db_session.query(Site)
                        .filter(Site.baseurl._in(not_in_server))
                        .all())
        for site in to_delete:
            g.db_session.delete(site)
        g.db_session.commit()

        # Gather tokens and siteinfo
        for site in new_sites:
            gather_tokens(site)
            gather_siteinfo(site)
        '''

    print 'Sites cross-referenced. Added %d sites:' % len(to_add)
    print '\t' + '\n\t'.join(to_add)


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
