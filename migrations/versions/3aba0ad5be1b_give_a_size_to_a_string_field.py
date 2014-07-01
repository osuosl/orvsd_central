"""Give a size to a string field

Revision ID: 3aba0ad5be1b
Revises: 40b2c7327c4
Create Date: 2014-07-01 16:28:36.282442

"""

# revision identifiers, used by Alembic.
revision = '3aba0ad5be1b'
down_revision = '40b2c7327c4'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.alter_table(table_name='sites_courses',
                   column_name='celery_task_id',
                   type_=String(255),
                   existing_type=String)

def downgrade_engine1():
     op.alter_table(table_name='sites_courses',
                   column_name='celery_task_id',
                   type_=String,
                   existing_type=String(255))

