"""increase password field length

Revision ID: 40b2c7327c4
Revises: 8534536b5e7
Create Date: 2014-04-14 14:23:25.570784

"""

# revision identifiers, used by Alembic.
revision = '40b2c7327c4'
down_revision = '8534536b5e7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String

def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.alter_column('users', 'password', nullable=False, type_=String(768))


def downgrade_engine1():
    pass

