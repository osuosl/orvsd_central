"""add_api_key_to_sites

Revision ID: 3a8b0a0fc61a
Revises: 543e1413a4c4
Create Date: 2013-07-30 22:21:20.015745

"""

# revision identifiers, used by Alembic.
revision = '3a8b0a0fc61a'
down_revision = '543e1413a4c4'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.add_column('sites', sa.Column('api_key', sa.String(length=40)))

def downgrade_engine1():
    op.drop_column('sites', 'api_key')

