from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from orvsd_central.util import requires_role
from orvsd_central.util import app
import requests

mod = Blueprint('general', __name__)

@mod.route('/test/admin')
@requires_role('admin')
def test_role_admin():
    """Used to test the admin role. Returns HTTP code 200, OK"""
    return test_sub()


@mod.route('/test/helpdesk')
@requires_role('helpdesk')
def test_role_helpdesk():
    """Used to test the helpdesk role. Returns HTTP code 200, OK"""
    return test_sub()


@mod.route('/test/user')
@requires_role('user')
def test_role_user():
    """Used to test the user role. Returns HTTP code 200, OK"""
    return test_sub()


def test_sub():
    """return an HTTP 200 code with 'okay' as the body"""
    return 'okay'
