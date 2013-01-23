import unittest
import tempfile
import sqlalchemy

class ORVSD_Central_Tests(unittest.TestCase):
    def add_User(username, password, confirm_password, email, permission_level):
        return self.app.post('/register', data=dict(
            username=username,
            password=password,
            confirm_password=confirm_password,
            email=email,
            permission_level=permission_level
        ))

    def test_add_User():
        username = 'name'
        resp = self.add_User(user, 'password', 'password', 'confirm_password', 'email@orvsd.org', 'Admin')
        assert user+' has been added to the database successfully!' in resp.data
