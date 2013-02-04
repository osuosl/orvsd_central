"""empty message

Revision ID: 28028e01a6d0
Revises: 3cbf94b62f86
Create Date: 2013-01-31 18:03:55.020767

"""

# revision identifiers, used by Alembic.
revision = '28028e01a6d0'
down_revision = '3cbf94b62f86'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.create_foreign_key(name="fk_school_to_district_id", source="schools", referent="districts", local_cols=['district_id'], remote_cols=['id'])

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

