import mock
import unittest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from orvsd_central.database import db_session
import orvsd_central
from orvsd_central.models import User
from flask.ext.login import (login_user, logout_user)
from flask import redirect
from controllers import test_roles_controller



class TestRequiresRole(unittest.TestCase):

    def setUp(self):
        self.app = orvsd_central.app.test_client()
        self.app = orvsd_central.app
        orvsd_central.app.config['TESTING'] = True
        # Create web driver
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://localhost:5000/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_requires_role_decorator(self):
        with self.app.test_request_context(''):
            admin_user = User('admin', 'admin@example.com', 'password', role=3)
            login_user(admin_user)
            self.assertEqual('okay', test_roles_controller.test_role_admin())
            self.assertEqual('okay', test_roles_controller.test_role_helpdesk())
            self.assertEqual('okay', test_roles_controller.test_role_user())
            logout_user()

            helpdesk_user = User('helpdesk', 'helpdesk@example.com', 'password', role=2)
            login_user(helpdesk_user)
            # Check that the returned HTTP status code is 302, found.
            self.assertEqual(302, test_roles_controller.test_role_admin().status_code)
            self.assertEqual('okay', test_roles_controller.test_role_helpdesk())
            self.assertEqual('okay', test_roles_controller.test_role_user())
            logout_user()

            normal_user = User('normal', 'normal@example.com', 'password', role=1)
            login_user(normal_user)
            self.assertEqual(302, test_roles_controller.test_role_admin().status_code)
            self.assertEqual(302, test_roles_controller.test_role_helpdesk().status_code)
            self.assertEqual('okay', test_roles_controller.test_role_user())
            logout_user()
        #response = self.app.get('/tests/admin')
        #print 'data'
        #print response, type(response)
        #with self.app:
        #    resp1 = test_roles_controller.test_role_admin()
        #print resp, type(resp1)
        #a = 1
        #b  = 1 /0

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

