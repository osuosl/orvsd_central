from flask import Blueprint, render_template
from flask.ext.login import current_user, login_required
from sqlalchemy import distinct

from orvsd_central.models import Course, District, School, Site
from orvsd_central.util import build_accordion


mod = Blueprint("report", __name__, url_prefix='/report')


@mod.route("/", methods=['GET'])
@login_required
def index():
    """
    Returns a rendered template for the index/report page.
    """
    all_districts = District.query.order_by("name").all()
    dist_count = len(all_districts)
    school_count = School.query.count()
    site_count = Site.query.count()
    course_count = Course.query.count()

    stats = defaultdict(int)

    # Get sites we have details for.
    sds = db_session.query(SiteDetail.site_id).distinct()
    # Convert the single element tuple with a long, to a simple integer.
    for sd in map(lambda x: int(x[0]), sds):
        # Get each's most recent result.
        info = SiteDetail.query.filter_by(site_id=sd) \
                                      .order_by(SiteDetail
                                                .timemodified
                                                .desc()) \
                                      .first()

        stats['adminusers'] += info.adminusers or 0
        stats['teachers'] += info.teachers or 0
        stats['totalusers'] += info.totalusers or 0
        stats['activeusers'] += info.activeusers or 0

    accord_id = "dist_accord"
    dist_id = "distid=%s"

    data = build_accordion(all_districts, accord_id, "district", dist_id)

    return render_template("report.html",
                           datadump=data,
                           dist_count=dist_count,
                           school_count=school_count,
                           site_count=site_count,
                           course_count=course_count,
                           stats=stats,
                           user=current_user)


