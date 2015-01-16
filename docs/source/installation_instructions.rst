====
Setting up ORVSD Central
====
Pre-requisites:
----
In order to setup ORVSD_Central a Database Server is needed with a database called 'central'

Instructions
----
We recommend setting up orvsd_central in a virtualenv.

\1. After sourcing your virtualenv go to your directory which contains
orvsd_central and run::

    pip install -r requirements.txt

\2. Configure ORVSD Central

    cp config/default.py.dist config/default.py

Edit the options according to your environment

\3. Run the following manage.py command before any others::

    python manage.py setup_db

A prompt for an admin account creation will show, choose any
username, email, and password you wish.

\4. Import district and school data::

    python manage.py import_data -d /path/to/someData.csv

.. This instruction isn't complete until we find a way so the user doesn't need
    download the .csv file.

\5. Gather sitedetail data from existing moodle sites::

    python manage.py gather

\6. To run the server::

    python manage.py runserver

There you have it! Test your orvsd_central instance out by going to http://127.0.0.1:5000 in your browser.

