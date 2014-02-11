from flask import Blueprint, jsonify

from orvsd_central import db
from orvsd_central.models import Course, CourseDetail, Site

mod = Blueprint('api', __name__)


@mod.route("/courses/filter", methods=["POST"])
def get_course_list():
    dir = request.form.get('filter')

    if dir == "None":
        courses = CourseDetail.query.all()
    else:
        courses = db.session.query(CourseDetail).join(Course) \
                    .filter(Course.source == dir).all()

    # This means the folder selected was not the source folder or None.
    if not courses:
        courses = db.session.query(CourseDetail).filter(CourseDetail.filename
                                                        .like("%"+dir+"%"))\
                                                .all()

    courses = sorted(courses, key=lambda x: x.course.name)

    serialized_courses = [{'id': course.course_id,
                           'name': course.course.name}
                          for course in courses]
    return jsonify(courses=serialized_courses)


@mod.route('/get_site_by/<int:site_id>', methods=['GET'])
def site_by_id(site_id):
    name = Site.query.filter_by(id=site_id).first().name
    return jsonify(name=name)
