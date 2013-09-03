"""Add course information to Celery tasks list in database.

Revision ID: 3c4abb6a4665
Revises: 543e1413a4c4
Create Date: 2013-09-03 14:40:58.995837

"""

# revision identifiers, used by Alembic.
revision = '3c4abb6a4665'
down_revision = '543e1413a4c4'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.add_column('course_details', sa.Column('moodle_course_id', sa.Integer))


def downgrade(engine_name):
    op.drop_column('course_details', 'moodle_course_id')


def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

