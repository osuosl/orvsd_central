from flask import Blueprint, render_template
from flask.ext.login import current_user, login_required

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

    active_accord_id = "dist_accord_active"
    inactive_accord_id = "dist_accord_inactive"
    dist_id = "distid=%s"

    data = build_accordion(all_districts, active_accord_id,
                           inactive_accord_id, "district", dist_id)

    return render_template("report.html",
                           datadump=data,
                           user=current_user)
