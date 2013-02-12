"""empty message

Revision ID: 37c8daee72b6
Revises: 345f42be80fd
Create Date: 2013-01-28 17:10:33.656857

"""

# revision identifiers, used by Alembic.
revision = '37c8daee72b6'
down_revision = '345f42be80fd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade(engine_name):
    op.drop_column('schools', 'disctrict_id')    
def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

