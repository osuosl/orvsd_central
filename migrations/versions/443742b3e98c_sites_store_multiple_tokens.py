"""sites store multiple tokens

Revision ID: 443742b3e98c
Revises: 17f527a3ed3a
Create Date: 2014-12-08 18:45:00.187657

"""

# revision identifiers, used by Alembic.
revision = '443742b3e98c'
down_revision = '17f527a3ed3a'

from collections import defaultdict
import json

from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy import String
import sqlalchemy as sa

from orvsd_central.models import Site


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    # Get the connection to do some non-mapped queries
    connection = op.get_bind()

    # site.id: tokens as {}
    site_tokens = defaultdict(dict)

    # Manual sites query
    sql = "SELECT id,api_key FROM sites;"

    # Execute the query
    results = connection.execute(sql)

    # Gather the installcourse token for each site, if one exists
    for site in results:
        # If a token existed, add it to the dict
        if site.api_key:
            site_tokens[site.id]['orvsd_installcourse'] = site.api_key

    # Alter the column name and size
    op.alter_column(
        'sites',
        column_name='api_key',
        new_column_name='moodle_tokens',
        existing_type=String(40),
        type_=String(2048)
    )

    # Session for commiting altered data
    session = Session(bind=op.get_bind())

    # Commit the alter column
    session.commit()

    # for each site, either dump an empty dict (yay default dict) or dump
    # json with the orvsd_installcourse token
    for site in session.query(Site):
        site.moodle_tokens = json.dumps(site_tokens[site.id])

    # Commit all to the database
    session.commit()


def downgrade_engine1():
    # Get the connection to do some non-mapped queries
    connection = op.get_bind()

    # site.id: tokens as {}
    site_tokens = defaultdict(dict)

    # Manual sites query
    sql = "SELECT id,moodle_tokens FROM sites;"

    # Execute the query
    results = connection.execute(sql)

    # A mapping of site_id to orvsd_installcourse token
    site_tokens = defaultdict(str)

    # Collect any tokens
    for site in results:
        current_tokens = json.loads(site.moodle_tokens)
        site_tokens[site.id] = current_tokens.get('orvsd_installcourse', '')

    # Now we have a backup of the tokens to keep, alter the column
    op.alter_column(
        'sites',
        column_name='moodle_tokens',
        new_column_name='api_key',
        existing_type=String(2048),
        type_=String(40)
    )

    # Start a session for data migration
    session = Session(bind=op.get_bind())

    # Commit the altered column
    session.commit()

    # Apply the tokens to the downgraded column
    for site in session.query(Site):
        # Update the column
        site.api_key = site_tokens[site.id]

    # Commit chages to the database
    session.commit()
