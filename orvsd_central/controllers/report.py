from flask import Blueprint, g, render_template
from flask.ext.login import current_user, login_required
from sqlalchemy.sql import func
from orvsd_central.models import SiteDetail

import time

mod = Blueprint("report", __name__, url_prefix='/report')


@mod.route("/", methods=['GET'])
@login_required
def index():
    """
    Returns a rendered template for the index/report page.
    """

    date_active_since = g.db_session.query(
        func.max(SiteDetail.timemodified)
    ).first()[0]
    active_since = time.strftime("%b %d, %Y", date_active_since.timetuple())

    return render_template("report.html",
                           user=current_user,
                           active_since=active_since)
