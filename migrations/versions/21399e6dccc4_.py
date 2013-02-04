"""empty message

Revision ID: 21399e6dccc4
Revises: 14b1465049b9
Create Date: 2013-01-31 17:48:31.049383

"""

# revision identifiers, used by Alembic.
revision = '21399e6dccc4'
down_revision = '14b1465049b9'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    #op.create_foreign_key(name="fk_school_to_district_id", source="districts", referent="schools", local_cols=['id'], remote_cols=['district_id'])
    op.drop_constraint(name='fk_school_to_district_id', tablename='districts', type='foreignkey')
def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

