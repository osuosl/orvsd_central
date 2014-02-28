"""Added students to sites_courses

Revision ID: 1b73cba31aaa
Revises: 327d34d886b4
Create Date: 2014-02-28 10:59:43.712776

"""

# revision identifiers, used by Alembic.
revision = '1b73cba31aaa'
down_revision = '327d34d886b4'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.add_column('sites_courses', sa.Column('students', sa.Integer))


def downgrade_engine1():
    op.drop_column('sites_courses', 'students')

