How to run automated tests
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
