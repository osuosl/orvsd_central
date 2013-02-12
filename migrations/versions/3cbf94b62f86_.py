"""empty message

Revision ID: 3cbf94b62f86
Revises: 21399e6dccc4
Create Date: 2013-01-31 18:02:48.955683

"""

# revision identifiers, used by Alembic.
revision = '3cbf94b62f86'
down_revision = '21399e6dccc4'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.drop_constraint(name='fk_school_to_district_id', tablename='districts', type='foreignkey')

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

