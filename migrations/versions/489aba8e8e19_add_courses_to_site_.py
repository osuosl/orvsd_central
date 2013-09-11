"""add courses to site_details

Revision ID: 489aba8e8e19
Revises: 6bf51fc87fa
Create Date: 2013-02-28 16:04:04.646625

"""

# revision identifiers, used by Alembic.
revision = '489aba8e8e19'
down_revision = '6bf51fc87fa'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.add_column('site_details', sa.Column('courses', sa.Text()))

def downgrade_engine1():
    op.drop_column('site_details', 'courses')
