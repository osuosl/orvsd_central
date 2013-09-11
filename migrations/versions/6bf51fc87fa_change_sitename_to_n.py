"""change sitename to name

Revision ID: 6bf51fc87fa
Revises: 552d37db1d09
Create Date: 2013-02-26 16:45:00.353724

"""

# revision identifiers, used by Alembic.
revision = '6bf51fc87fa'
down_revision = '552d37db1d09'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()

def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.alter_column(table_name='sites',
                    column_name='sitename',
                    name='name',
                    existing_type=sa.String(255))

def downgrade_engine1():
    op.alter_column(table_name='sites',
                    column_name='name',
                    name='sitename')
