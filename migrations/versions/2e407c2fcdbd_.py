"""empty message

Revision ID: 2e407c2fcdbd
Revises: 37c8daee72b6
Create Date: 2013-01-31 09:12:55.487827

"""

# revision identifiers, used by Alembic.
revision = '2e407c2fcdbd'
down_revision = '37c8daee72b6'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.drop_constraint(name = 'schools_ibfk_1', tablename = 'schools', type = 'foreignkey')

    #op.drop_column('schools', 'disctrict_id')

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.drop_column('schools', 'disctrict_id')

def downgrade_engine1():
    pass

