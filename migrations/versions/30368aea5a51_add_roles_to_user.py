"""Add roles to User

Revision ID: 30368aea5a51
Revises: 3a8b0a0fc61a
Create Date: 2013-08-29 18:28:31.888475

"""

# revision identifiers, used by Alembic.
revision = '30368aea5a51'
down_revision = '3a8b0a0fc61a'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    op.add_column('users', sa.Column('role', sa.SmallInteger))


def downgrade(engine_name):
    op.drop_column('users', 'role')





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

