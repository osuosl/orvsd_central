"""add moodle_course_id

Revision ID: 543e1413a4c4
Revises: 489aba8e8e19
Create Date: 2013-07-30 20:18:43.101882

"""

# revision identifiers, used by Alembic.
revision = '543e1413a4c4'
down_revision = '489aba8e8e19'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.add_column('course_details', sa.Column('moodle_course_id', sa.Integer))

def downgrade_engine1():
    op.drop_column('course_details', 'moodle_course_id')
