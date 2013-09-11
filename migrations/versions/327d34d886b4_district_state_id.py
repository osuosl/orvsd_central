"""District.state_id

Revision ID: 327d34d886b4
Revises: 3a8b0a0fc61a
Create Date: 2013-09-10 16:56:54.916953

"""

# revision identifiers, used by Alembic.
revision = '327d34d886b4'
down_revision = '3a8b0a0fc61a'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()



def upgrade_engine1():
    op.add_column('districts', sa.Column('state_id', sa.Int()))

def downgrade_engine1():
    op.drop_column('districts', 'state_id')
