"""add state id to schools

Revision ID: 2e95d1cc3baf
Revises: 55f18cc1b2de
Create Date: 2013-09-11 20:51:53.269177

"""

# revision identifiers, used by Alembic.
revision = '2e95d1cc3baf'
down_revision = '3a8b0a0fc61a'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.add_column('schools', sa.Column('state_id', sa.Integer))


def downgrade_engine1():
    op.drop_column('schools', 'state_id')

