"""collapse course

Revision ID: 506c416e8750
Revises: 2bf8713fd2bb
Create Date: 2015-03-12 12:27:10.979305

"""

# revision identifiers, used by Alembic.
revision = '506c416e8750'
down_revision = '2bf8713fd2bb'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

from orvsd_central.models import Course, SiteCourse


class CourseDetail(sa.ext.declarative.declarative_base()):
    """
    A Model representation of a Course's details.

    id               : Unique to orvsd
    course_id        : Unique to orvsd
    filename         : The name and extension without the full path
    version          : The version, format determined by client
    updated          : Time of the last update
    active           : True if the course has recently been in use
    moodle_version   : A moodle style version
    moodle_course_id : The course id determined by moodle
    """

    __tablename__ = 'course_details'
    id = sa.Column(sa.Integer, primary_key=True)
    course_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            'courses.id', use_alter=True, name='fk_course_details_site_id'
        )
    )
    filename = sa.Column(sa.String(255))
    version = sa.Column(sa.Float)
    updated = sa.Column(sa.DateTime)
    active = sa.Column(sa.Boolean)
    moodle_version = sa.Column(sa.String(255))
    moodle_course_id = sa.Column(sa.Integer)


def upgrade(engine_name):
    eval("upgrade_%s" % engine_name)()


def downgrade(engine_name):
    eval("downgrade_%s" % engine_name)()


def upgrade_engine1():
    # Grab the session, we will need to commit along the way
    session = Session(bind=op.get_bind())

    # Begin by dropping the celery_task_id column
    op.drop_column('sites_courses', 'celery_task_id')

    # Modify many from String(255) to Text
    op.alter_column('courses', 'name',
                    type_=sa.Text, existing_type=sa.String(255),)
    op.alter_column('courses', 'category',
                    type_=sa.Text, existing_type=sa.String(255),)
    op.alter_column('courses', 'license',
                    type_=sa.Text, existing_type=sa.String(255),)
    op.alter_column('courses', 'source',
                    type_=sa.Text, existing_type=sa.String(255),)

    # Add all the new columns to Course
    op.add_column('courses', sa.Column('filename', sa.Text))
    op.add_column('courses', sa.Column('moodle_course_id', sa.Integer))
    op.add_column('courses', sa.Column('moodle_version', sa.Text))
    op.add_column('courses', sa.Column('updated', sa.DateTime))
    op.add_column('courses', sa.Column('version', sa.Float))

    # Commit as it is time to begin a data migration
    session.commit()

    # Grab the latest updated course detail for a given course and combine the
    # two rows into one new Course row
    for course in session.query(Course).all():
        # detail == course_details row
        detail = session.query(CourseDetail).filter(
            CourseDetail.course_id == course.id
        ).order_by(CourseDetail.updated.desc()).first()

        # Update row with new data
        course.filename = detail.filename
        course.moodle_course_id = detail.moodle_course_id
        course.moodle_version = detail.moodle_version
        course.updated = detail.updated
        course.version = detail.version

        session.add(course)

    # Commit the changes to course
    session.commit()


def downgrade_engine1():
    # Grab the session, we will need to commit along the way
    session = Session(bind=op.get_bind())

    # Begin by restoring the celery_task_id column
    op.add_column('sites_courses', sa.Column('celery_task_id', sa.String(255)))

    # (Potentially) Truncate columns
    op.alter_column('courses', 'name',
                    type_=sa.String(255), existing_type=sa.Text)
    op.alter_column('courses', 'category',
                    type_=sa.String(255), existing_type=sa.Text)
    op.alter_column('courses', 'license',
                    type_=sa.String(255), existing_type=sa.Text)
    op.alter_column('courses', 'source',
                    type_=sa.String(255), existing_type=sa.Text)

    # Commit as it is time to begin a data migration
    session.commit()

    # For each course, split into Course and CourseDetail
    for course in session.query(Course).all():
        # Create a CourseDetail with necessary data from course
        course_detail = CourseDetail(
            course_id=course.id,
            filename=course.filename,
            version=course.version,
            updated=course.updated,
            active=False,
            moodle_version=course.moodle_version,
            moodle_course_id=course.moodle_course_id,
        )

        session.add(course_detail)

    # Commit the course details
    session.commit()

    # Drop all the unused columns from Course
    op.drop_column('courses', 'filename')
    op.drop_column('courses', 'moodle_course_id')
    op.drop_column('courses', 'moodle_version')
    op.drop_column('courses', 'updated')
    op.drop_column('courses', 'version')

