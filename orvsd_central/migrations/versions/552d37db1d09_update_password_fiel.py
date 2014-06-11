"""update password field for hashing

Revision ID: 552d37db1d09
Revises: None
Create Date: 2013-02-25 17:21:20.709136

"""

# revision identifiers, used by Alembic.
revision = '552d37db1d09'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.alter_column(table_name='users',
                    column_name='password',
                    type_=sa.String(255))

def downgrade_engine1():
    pass
