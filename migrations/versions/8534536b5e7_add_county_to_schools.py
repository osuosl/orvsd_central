"""add county to schools

Revision ID: 8534536b5e7
Revises: 1b73cba31aaa
Create Date: 2014-03-19 18:10:25.755029

"""

# revision identifiers, used by Alembic.
revision = '8534536b5e7'
down_revision = '1b73cba31aaa'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.add_column('schools', sa.Column('county', sa.String(255)))


def downgrade_engine1():
    op.drop_column('schools', 'county')

