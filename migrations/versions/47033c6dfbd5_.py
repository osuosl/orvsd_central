"""empty message

Revision ID: 47033c6dfbd5
Revises: None
Create Date: 2013-01-14 19:30:24.103274

"""

# revision identifiers, used by Alembic.
revision = '47033c6dfbd5'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

