from flask import Blueprint, render_template
from flask.ext.login import current_user, login_required

mod = Blueprint("report", __name__, url_prefix='/report')


@mod.route("/", methods=['GET'])
@login_required
def index():
    """
    Returns a rendered template for the index/report page.
    """

    return render_template("report.html",
                           user=current_user)
