#Alembic logs for migration: note the lack of any autogenerated upgrade script
#
#INFO  [alembic.migration] Context impl MySQLImpl.
#INFO  [alembic.migration] Will assume non-transactional DDL.
#INFO  [alembic.autogenerate] Detected removed column 'course_details.parent_id'



"""empty message

Revision ID: 53a608373b2f
Revises: None
Create Date: 2013-02-07 17:09:41.085350

"""

# revision identifiers, used by Alembic.
revision = '53a608373b2f'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass
