"""empty message

Revision ID: 48067400c734
Revises: None
Create Date: 2013-01-25 15:48:39.062272

"""

# revision identifiers, used by Alembic.
revision = '48067400c734'
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

