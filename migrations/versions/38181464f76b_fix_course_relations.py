"""fix course relationships

Revision ID: 38181464f76b
Revises: 1d4a29b9a083
Create Date: 2013-02-06 17:37:17.972638

"""

# revision identifiers, used by Alembic.
revision = '38181464f76b'
down_revision = '1d4a29b9a083'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade(engine_name):
    op.execute("ALTER TABLE course_details ADD id INT PRIMARY KEY AUTO_INCREMENT;")
    op.execute("ALTER TABLE course_details DROP course_id;")
    op.add_column('course_details', Column('course_id', String()))
    op.create_foreign_key(name='fk_course_details_course_id', source='course_details', referent='courses', local_cols=['course_id'], remote_cols=['id'])

def downgrade(engine_name):
    op.execute("ALTER TABLE course_details DROP id;")
    op.execute("ALTER TABLE course_details ADD course_id INT PRIMARY KEY AUTO_INCREMENT;")





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

