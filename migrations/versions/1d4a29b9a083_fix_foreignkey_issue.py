"""fix ForeignKey issues

Revision ID: 1d4a29b9a083
Revises: 28028e01a6d0
Create Date: 2013-02-01 14:46:06.373104

"""

# revision identifiers, used by Alembic.
revision = '1d4a29b9a083'
down_revision = '28028e01a6d0'

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
#    op.drop_constraint(name='sites_courses_ibfk_1', tablename='sites_courses', type='foreignkey')
#    op.create_foreign_key(name="fk_sites_courses_site_id", source='sites_courses', referent='sites', local_cols=['site_id'], remote_cols=['id'])
 #   op.drop_constraint(name='sites_courses_ibfk_2', tablename='sites_courses', type='foreignkey')
  #  op.create_foreign_key(name="fk_sites_courses_course_id", source='sites_courses', referent='courses', local_cols=['course_id'], remote_cols=['id'])
#    op.drop_constraint(name='site_details_ibfk_1', tablename='site_details', type='foreignkey')
    op.create_foreign_key(name='fk_site_details_site_id', source='site_details', referent='sites', local_cols=['site_id'], remote_cols=['id'])
    op.drop_constraint(name='sites_ibfk_1', tablename='sites', type='foreignkey')
    op.create_foreign_key(name='fk_sites_school_id', source='sites', referent='schools', local_cols=['school_id'], remote_cols=['id'])


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()





def upgrade_engine1():
    pass


def downgrade_engine1():
    pass

