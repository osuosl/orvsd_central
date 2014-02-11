from flask import Blueprint, jsonify

from orvsd_central.models import Site

mod = Blueprint('api', __name__)


@mod.route('/get_site_by/<int:site_id>', methods=['GET'])
def site_by_id(site_id):
    name = Site.query.filter_by(id=site_id).first().name
    return jsonify(name=name)
