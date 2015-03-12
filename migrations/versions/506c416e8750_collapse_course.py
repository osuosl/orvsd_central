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
    # Begin by dropping the celery_task_id column
    op.drop_column('sites_courses', 'celery_task_id')

    # Modify many from String(255) to Text
    op.alter_column('courses', 'name',
                    type_=sa.Text, existing_type=sa.String(255),)
    op.alter_column('courses', 'category',
                    type_=sa.Text, existing_type=sa.String(255),)
    op.alter_column('courses', 'license',
                    type_=sa.Text, existing_type=sa.String(255),)
    op.alter_column('courses', 'source',
                    type_=sa.Text, existing_type=sa.String(255),)


def downgrade_engine1():
    # Begin by restoring the celery_task_id column
    op.add_column('sites_courses', sa.Column('celery_task_id', sa.String(255)))

    # (Potentially) Truncate columns
    op.alter_column('courses', 'name',
                    type_=sa.String(255), existing_type=sa.Text)
    op.alter_column('courses', 'category',
                    type_=sa.String(255), existing_type=sa.Text)
    op.alter_column('courses', 'license',
                    type_=sa.String(255), existing_type=sa.Text)
    op.alter_column('courses', 'source',
                    type_=sa.String(255), existing_type=sa.Text)
