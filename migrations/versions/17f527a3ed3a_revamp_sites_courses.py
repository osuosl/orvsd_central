"""revamp sites_courses

Revision ID: 17f527a3ed3a
Revises: 3aba0ad5be1b
Create Date: 2014-10-09 18:48:32.271193

"""

# revision identifiers, used by Alembic.
revision = '17f527a3ed3a'
down_revision = '3aba0ad5be1b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('sites_courses', 'celery_task_id')
    op.drop_column('sites_courses', 'students')
    op.add_column('sites_courses', sa.Column('celery_task_id', sa.String(255))


def downgrade():
    op.drop_column('sites_courses', 'celery_task_id')
    op.add_column('sites_courses', sa.Column('students', sa.Integer)
    op.add_column('sites_courses', sa.Column(
        'celery_task_id',
        sa.ForeignKey(
            'celery_taskmeta.task_id',
            use_alter=True,
            name='fk_sites_courses_celery_task_id'
        )
    )
