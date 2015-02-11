"""adminemail to adminlist

Revision ID: 49e0d0a0a952
Revises: 443742b3e98c
Create Date: 2015-01-30 10:47:48.272240

"""

# revision identifiers, used by Alembic.
revision = '49e0d0a0a952'
down_revision = '443742b3e98c'

from collections import defaultdict
import json

from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy import Text
import sqlalchemy as sa

from orvsd_central.models import SiteDetail


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    # Drop the adminemail and add the adminlist columns
    op.drop_column('site_details', 'adminemail')
    op.add_column('site_details', sa.Column('adminlist', Text()))

    # Initialize each adminlist as an empty json object
    session = Session(bind=op.get_bind())
    for details in session.query(SiteDetail):
        details.adminlist = "{}"

    session.commit()


def downgrade_engine1():
    # Drop the adminlist and add the adminemail columns
    op.drop_column('site_details', 'adminlist')
    op.add_column('site_details', sa.Column('adminemail', String(255)))
