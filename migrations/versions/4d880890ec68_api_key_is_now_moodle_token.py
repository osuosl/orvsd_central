"""api_key is now moodle_token

Revision ID: 4d880890ec68
Revises: 17f527a3ed3a
Create Date: 2014-11-12 15:12:47.760777

"""

# revision identifiers, used by Alembic.
revision = '4d880890ec68'
down_revision = '17f527a3ed3a'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.alter_column('sites', column_name='api_key', new_column_name='moodle_toke')


def downgrade_engine1():
    op.alter_column('sites', column_name='moodle_token', new_column_name='api_key')

