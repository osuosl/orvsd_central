"""Add ID to sites_courses

Revision ID: 9ff028d61e9
Revises: 4558bd24a6f8
Create Date: 2013-09-16 15:16:32.375512

"""

# revision identifiers, used by Alembic.
revision = '9ff028d61e9'
down_revision = '4558bd24a6f8'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    # Alembic doesn't actually support adding primary keys to an existing table
    # (due to potentially unexpected behavior), but sites_courses is empty at
    # the time of this migration.
    op.execute("ALTER TABLE sites_courses ADD id INT PRIMARY KEY
            AUTO_INCREMENT;")


def downgrade(engine_name):
    op.execute("ALTER TABLE sites_courses DROP COLUMN id;")




def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

