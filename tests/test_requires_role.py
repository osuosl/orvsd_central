import mock
import unittest
import tempfile
import time
import re
import os
from orvsd_central import models
from orvsd_central import util


class TestRequiresRole(unittest.TestCase):

    def setUp(self):
        # Init database
        from orvsd_central import db, models
        db.Metadata.create_all()
        # Create web driver
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_requires_role_decorator(self):
        # Mock out the Flask redirect function
        redirect = mock.Mock(return_value=False)
        current_user = mock.Mock()
        # Define local methods decorated
        # at the permission levels we are testing.

        @util.requires_role('admin')
        def test_admin():
            return true

        @util.requires_role('helpdesk')
        def test_helpdesk():
            return true

        @util.requires_role('user')
        def test_user():
            return true

        #We also need to test invalid permission levels.
        @util.requires_role('gibberish')
        def test_gibberish():
            return true
        # We need to test that users can enter
        # the parts they are supposed to
        # and also that they cannot enter the parts
        # they are not supposed to.
        # Test admin
        current_user.role = 'admin'
        self.assertTrue(test_admin())
        self.assertTrue(test_helpdesk())
        self.assertTrue(test_user())
        self.assertFalse(test_gibberish())
        # Test helpdesk
        current_user.role = 'helpdesk'
        self.assertTrue(test_helpdesk())
        self.assertTrue(test_user())
        self.assertFalse(test_gibberish())
        self.assertFalse(test_admin())
        # Test user
        current_user.role = 'user'
        self.assertTrue(test_user())
        self.assertFalse(test_gibberish())
        self.assertFalse(test_admin())
        self.assertFalse(test_helpdesk())
