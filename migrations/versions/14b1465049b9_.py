"""empty message

Revision ID: 14b1465049b9
Revises: 2e407c2fcdbd
Create Date: 2013-01-31 17:43:33.322526

"""

# revision identifiers, used by Alembic.
revision = '14b1465049b9'
down_revision = '2e407c2fcdbd'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.alter_column(table_name='schools', column_name='disctrict_id', name = 'district_id', existing_type=sa.Integer)

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

