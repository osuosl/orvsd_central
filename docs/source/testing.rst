How to Run Automated Tests
============

Use the following commands

.. code-block:: text

  source /opt/orvsd-virtualenv/bin/activate
  cd <path/to/orvsd_central>
  PYTHONPATH='.' nosetests tests/<test_file>.py

-----

Example:

.. code-block:: text

  source /opt/orvsd-virtualenv/bin/activate
  cd /var/www/orvsd_central
  PYTHONPATH='.' nosetests tests/test_the_feature.py

Writing Tests: A HOWTO by Example
=================================

The following will walk through a few scenarios for writing tests
for ORVSD Central

To begin writing tests, take note of tests/base.py, you will want to
use it and the features it provides to make testing easy

Our first example:

.. code-block:: python

   """
   The hello world test
   """

   # Be sure to use the TestBase class provided by tests/base.py
   from base import TestBase

   # Inherit TestBase to make testing easy
   class HelloTest(TestBase):

       def test_hello(self):
           self.assertEqual("hello","hello")

Simple enough, right? Now lets do something basic with the
ORVSD Central app

.. code-block:: python

   from base import TestBase

   class ValidEmailTest(TestBase):

       # Lets write a simple test for the util function is_valid_email
       def test_valid_email(self):
           # All imports need to happen at the method level for them to
           # be context aware
           from orvsd_central.util import is_valid_email

           email = 'niceandsimple@example.com'

           self.assertTrue(is_valid_email(email))

Ok, that too is neat, but how about testing methods that use the database?

.. code-block:: python

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

A neat feature of the decorator is that it also takes care of tearing down the
database for us as well.

**NOTE**: One downfall of the decorator in its current state is that the database
objects must be committed at the method level as well. In setUp you can create,
say, self.user = User(...), however, in each test you use that user you will
need to `g.db_session.add(user); g.db_session.commit()`

Something a bit more advanced can be done with the setUp method, howerver. A
test may modify the configuration options of the app

.. code-block:: python

   from base import TestBase

   class ExampleSetupTest(TestBase):

       def setUp(self):
           # Simply create a dictionary with the new configuration options
           config = {
               'SECRET_KEY': 'new super secret test key'
           }

           # Then call super
           super(ExampleSetupTest, self).setUp(test_cfg_changes=config)

       # How do we know these changes worked? Lets write a test!
       def test_setup_config(self):
           key = self.app.config['SECRET_KEY']

           # And let's assert it's equal to what we said it should be in setUp
           self.assertEqual(key, 'new super secret test key')
