from collections import defaultdict
import json

from flask import Blueprint, abort, g, jsonify, request

from orvsd_central.models import (Course, CourseDetail, District, School, Site,
                                  SiteDetail)
from orvsd_central.util import (get_obj_by_category, get_obj_identifier,
                                get_schools, string_to_type)


mod = Blueprint('api', __name__, url_prefix="/1")


@mod.route("/<category>/object/add", methods=["POST"])
def add_object(category):
    """
    Adds an object from a given Category to the database.

    get_obj_by_category will determine which category the submitted form
    is for.

    Returns:
        JSON response with the new object ID and a message on success or
        failure.
    """
    obj = get_obj_by_category(category)
    if obj:
        identifier = get_obj_identifier(category)
        inputs = {}
        # Here we update our dict with new values
        # A one liner is too messy :(
        for column in obj.__table__.columns:
            if column.name is not 'id':
                inputs.update({column.name: string_to_type(
                               request.form.get(column.name))})

        new_obj = obj(**inputs)
        g.db_session.add(new_obj)
        g.db_session.commit()
        return jsonify({'id': new_obj.id,
                        'identifier': identifier,
                        identifier: inputs[identifier],
                        'message': "Object added successfully!"})

    abort(404)


@mod.route("/<category>/<id>/delete", methods=["POST"])
def delete_object(category, id):
    """
    Given an 'category' and 'id' deletes the given object from the db.
    """
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=request.form.get("id")).first()
        if modified_obj:
            g.db_session.delete(modified_obj)
            g.db_session.commit()
            return jsonify({'message': "Object deleted successfully!"})

    abort(404)


# Get all task IDs
# TODO: Needs testing
@mod.route('/celery/id/all')
def get_all_ids():
    """
    Returns JSONified metadata for all celery tasks.
    """
    # TODO: "result" is another column, but SQLAlchemy
    # complains of some encoding error.
    statuses = g.db_session.query(
        "id", "task_id", "status", "date_done", "traceback"
    ).from_statement("SELECT * FROM celery_taskmeta").all()

    return jsonify(status=statuses)


@mod.route("/<category>/<id>/update", methods=["POST"])
def update_object(category, id):
    """
    Given an 'category' and 'id' updates the given object with data included
    in the form.
    """

    obj = get_obj_by_category(category)
    identifier = get_obj_identifier(category)
    if obj:
        modified_obj = obj.query.filter_by(id=request.form.get("id")).first()
        if modified_obj:
            inputs = {}

            # Here we update our dict with new
            for key in modified_obj.serialize().keys():
                inputs[key] = string_to_type(request.form.get(key))

            g.db_session.query(obj).filter_by(
                id=request.form.get("id")
            ).update(inputs)
            g.db_session.commit()

            return jsonify({'identifier': identifier,
                            identifier: inputs[identifier],
                            'message': "Object updated successfully!"})

    abort(404)


@mod.route("/site/<site_id>/courses")
def get_courses_by_site(site_id):
    """
    Returns a JSONified list of course details from the most recent
    site_details object for a given site_id.
    """
    # SiteDetails hold the course information we are looking for
    site_details = SiteDetail.query.filter_by(site_id=site_id) \
                                   .order_by(SiteDetail
                                             .timemodified
                                             .desc()) \
                                   .first()

    if site_details and site_details.courses:
        return jsonify(content=json.loads(site_details.courses))
    elif not site_details:
        return jsonify({'error:': 'Site not found.'})
    else:
        return jsonify({'error:': 'No courses found.'})


@mod.route("/courses/filter", methods=["POST"])
def get_course_list():
    """
    This returns a JSONified list of courses in a given folder, that is
    provided in the 'filter' form element.
    """
    dir = request.form.get('filter')

    if dir == "None":
        courses = CourseDetail.query.all()
    else:
        courses = g.db_session.query(CourseDetail).join(Course).filter(
            Course.source == dir
        ).all()

    # This means the folder selected was not the source folder or None.
    if not courses:
        courses = g.db_session.query(CourseDetail).filter(
            CourseDetail.filename.like("%"+dir+"%")
        ).all()

    courses = sorted(courses, key=lambda x: x.course.name)

    serialized_courses = [{'id': course.course_id,
                           'name': course.course.name}
                          for course in courses]
    return jsonify(courses=serialized_courses)


@mod.route("/<category>/keys")
def get_keys(category):
    """
    Returns a JSONified dict of all model attributes for a given model.
    """
    obj = get_obj_by_category(category)
    if obj:
        cols = dict((column.name, '') for column in
                    obj.__table__.columns)
        return jsonify(cols)


@mod.route("/site/<baseurl>/moodle")
def get_moodle_sites(baseurl):
    """
    Returns a JSONified list of moodle site ids and names for sites that are
    part of a school with the given 'baseurl'.
    """
    school_id = Site.query.filter_by(baseurl=baseurl).first().school_id
    moodle_sites = Site.query.filter_by(school_id=school_id).all()
    data = [{'id': site.id, 'name': site.name} for site in moodle_sites]
    return jsonify(content=data)


@mod.route("/<category>/<int:id>", methods=["GET"])
def get_object(category, id):
    """
    Returns a JSONified dict of attributes on an object defined by it's 'id'
    and the 'category' (model) it is.
    """
    obj = get_obj_by_category(category)
    if obj:
        modified_obj = obj.query.filter_by(id=id).first()
        if modified_obj:
            return jsonify(modified_obj.serialize())

    abort(404)


@mod.route('/report/get_active_schools', methods=['POST'])
def get_active_schools():
    """
    Returns all active schools for a district.
    """
    # From the POST, we need the district id, or distid
    dist_id = request.form.get('distid')
    return get_schools(dist_id, True)


@mod.route('/report/get_inactive_schools', methods=['POST'])
def get_inactive_schools():
    """
    Returns all inactive schools for a district.
    """
    # From the POST, we need the district id, or distid
    dist_id = request.form.get('distid')
    return get_schools(dist_id, False)


@mod.route("/site/<string:baseurl>")
def get_site_by_url(baseurl):
    """
    Returns a combined JSONified of both Site and SiteDetail information
    for a given 'baseurl'.
    """
    site = Site.query.filter_by(baseurl=baseurl).first()
    if site:
        site_details = SiteDetail.query.filter_by(site_id=site.id) \
                                       .order_by(SiteDetail
                                                 .timemodified
                                                 .desc()) \
                                       .first()

        site_info = dict(site.serialize().items() +
                         site_details.serialize().items())

        return jsonify(content=site_info)
    return jsonify(content={'error': 'Site not found'})


@mod.route('/celery/status/<celery_id>')
def get_task_status(celery_id):
    """
    Returns a JSONified status of a celery job identified by 'celery_id'.
    """
    status = g.db_session.query("status").from_statement(
        "SELECT status FROM celery_taskmeta WHERE id=:celery_id"
    ).params(celery_id=celery_id).first()
    return jsonify(status=status)


@mod.route("/report/stats", methods=['GET'])
def report_stats():
    """
    Get the stats of active users, teachers, admins, districts, schools, sites,
    and the numebr of total users and available courses
    """

    active_data = get_schools(None, True)

    stats = {
        'districts': 0,
        'schools': 0,
        'sites': 0,
        'courses': Course.query.count(),
        'admins': 0,
        'teachers': 0,
        'totalusers': 0,
        'activeusers': 0
    }

    # Get sites we have details for.
    sds = g.db_session.query(SiteDetail.site_id).distinct()
    # Convert the single element tuple with a long, to a simple integer.
    for sd in map(lambda x: int(x[0]), sds):
        # Get each's most recent result.
        info = SiteDetail.query.filter_by(site_id=sd).order_by(
            SiteDetail.timemodified.desc()
        ).first()

        stats['admins'] += info.adminusers or 0
        stats['teachers'] += info.teachers or 0
        stats['totalusers'] += info.totalusers or 0
        stats['activeusers'] += info.activeusers or 0

    return jsonify(stats)


@mod.route('/get_site_by/<int:site_id>', methods=['GET'])
def site_by_id(site_id):
    """
    Returns a JSONified name of a site, identifed by it's 'site_id'.
    """
    name = Site.query.filter_by(id=site_id).first().name
    return jsonify(name=name)
