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

How to Write Tests
==================

An example

.. code-block:: python

 from base import TestBase

 class ATest(TestBase):

     def test_valid_email(self):
         """
         We *must* import from within an app context and each test
         method happens to be in a context thanks to setUp. This means
         imports must happen at the method level rather than at the
         module level
         """

         from orvsd_central.util import is_valid_email

         email = "niceandsimple@example.com"

         self.assertTrue(is_valid_email(email))


     def test_invalid_email(self):
         """
         The downside to context aware tests is that the method we are testing
         must be imported again
         """

         from orvsd_central.util import is_valid_email

         email = "Abc.example.com"

         self.assertFalse(is_valid_email(email))
