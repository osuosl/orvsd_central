"""sites store multiple tokens

Revision ID: 443742b3e98c
Revises: 4d880890ec68
Create Date: 2014-12-08 18:45:00.187657

"""

# revision identifiers, used by Alembic.
revision = '443742b3e98c'
down_revision = '4d880890ec68'

import json

from alembic import op
from sqlalchemy.orm import Session
import sqlalchemy as sa

from orvsd_central.models import Site


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    # Start a session for data migration
    session = Session(bind=op.get_bind())

    # Alter the column name
    op.alter_column('sites', column_name='moodle_token', new_column_name='moodle_tokens')

    # For each site, convert the field to json, and re-add the token
    # if it had one
    for site in session.query(Site):
        # Token object being dumped to the moodle_tokens column
        tokens = {}
        # Current token (if one exists)
        token = site.moodle_tokens

        # Given that moodle_tokens is not '' - add the token for the
        # named service
        if token:
            tokens['orvsd_installcourse'] = token

        # Update the column
        site.moodle_tokens = json.dumps(tokens)

    # Commit chages to the database
    session.commit()


def downgrade_engine1():
    # Start a session for data migration
    session = Session(bind=op.get_bind())

    # Alter the column name
    op.alter_column('sites', column_name='moodle_tokens', new_column_name='moodle_token')

    # For each site, get the orvsd_installcourse token, if there is one, and
    # replace the existing data with it, make it an empty string
    for site in session.query(Site):
        # orvsd_installcourse token (if one exists)
        token = site.moodle_tokens.get('orvsd_installcourse', None)

        # Update the column
        site.moodle_token = token or ''

    # Commit chages to the database
    session.commit()
