"""moodle_tokens default

Revision ID: 2bf8713fd2bb
Revises: 49e0d0a0a952
Create Date: 2015-03-06 14:33:12.044131

"""

# revision identifiers, used by Alembic.
revision = '2bf8713fd2bb'
down_revision = '49e0d0a0a952'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    op.alter_column(
        'sites', 'moodle_tokens',
        server_default="{}",
        existing_type=sa.String(2048),
    )


def downgrade_engine1():
    op.alter_column(
        'sites', 'moodle_tokens',
        server_default=None,
        existing_type=sa.String(2048),
    )
