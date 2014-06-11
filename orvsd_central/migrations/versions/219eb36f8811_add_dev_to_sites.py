"""add dev to sites

Revision ID: 219eb36f8811
Revises: 2e95d1cc3baf
Create Date: 2013-09-11 22:36:09.152291

"""

# revision identifiers, used by Alembic.
revision = '219eb36f8811'
down_revision = '2e95d1cc3baf'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    op.add_column('sites', sa.Column('dev', sa.Boolean))


def downgrade_engine1():
    op.drop_column('sites', 'dev')

