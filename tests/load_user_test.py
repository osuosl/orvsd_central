# A fancy decorator has been written that sets up a
# database that is context aware
from base import db_context, TestBase

# flask globals, we need the g
from flask import g

class LoadUserTest(TestBase):

    # Test whether or not load_user is, well, returning the correct user
    @db_context  # Our fancy decorator that says we need a database
    def test_load_user(self):
        # Remember, imports that require a context must occur
        # at the method level
        from orvsd_central.models import User
        from orvsd_central.util import load_user

        # A test user
        user = User(
            name='test', email='te@st.com', password='hunter2', role=1
        )

        # Just like in ORVSD Central itself, we use g.db_session
        # to access the database
        g.db_session.add(user)
        g.db_session.commit()

        # Get the user id
        uid = user.id

        # Now that all the setup is done, time to test load_user
        self.assertEqual(uid, load_user(uid).id)