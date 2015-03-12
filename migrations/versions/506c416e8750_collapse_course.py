"""collapse course

Revision ID: 506c416e8750
Revises: 2bf8713fd2bb
Create Date: 2015-03-12 12:27:10.979305

"""

# revision identifiers, used by Alembic.
revision = '506c416e8750'
down_revision = '2bf8713fd2bb'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.drop_column('sites_courses', 'celery_task_id')


def downgrade_engine1():
    op.add_column('sites_courses', Column('celery_task_id', sa.String(255)))

