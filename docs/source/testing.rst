How to run automated tests
============

Use the following commands

.. code-block:: bash

  source /opt/orvsd-virtualenv/bin/activate
  cd <path/to/orvsd/trunk>
  PYTHONPATH='.' nosetests tests/<test_file>.py

-----

Example:

.. code-block:: bash

  source /opt/orvsd-virtualenv/bin/activate
  cd /var/www/orvsd_central
  PYTHONPATH='.' nosetests tests/test_the_feature.py
