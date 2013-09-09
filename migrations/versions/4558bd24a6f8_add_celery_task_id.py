"""Add Celery task ID

Revision ID: 4558bd24a6f8
Revises: 3a8b0a0fc61a
Create Date: 2013-09-09 16:39:25.746295

"""

# revision identifiers, used by Alembic.
revision = '4558bd24a6f8'
down_revision = '3a8b0a0fc61a'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.add_column('sites_courses', sa.Column('celery_task_id', sa.Text()))


def downgrade(engine_name):
    op.drop_column('sites_courses', 'celery_task_id')





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

