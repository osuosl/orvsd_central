Configuration Options
=====================

Flask
-----

DEBUG

- Enable debug output

CSRF_ENABLED

- Enable or disable CSRF with True/False

CSRF_SESSION_KEY

- Server side CSRF secret

SQLAlchemy
----------

SQLALCHEMY_DATABASE_URI

- A valid SQLAlchemy database uri where your database for orvsd_central is located

DATABASE_CONNECTION_OPTIONS

- A key/value dictionary of additional options for the database connection

SQLALCHEMY_MIGRATE_REPO

- Location of database migrations relative to the project folder by default

Celery Tasks
------------

CELERY_BROKER_URL

- Celery broker database URL. If using a database for the broker, be sure to prepend the address with sqla+

CELERY_RESULT_BACKEND

- Type of backend being used by celery.

CELERY_RESULT_DBURI

- Celery result database lacation

Database Server of Moodle Databases
-----------------------------------

SITEINFO_DATABASE_HOST

- Host for the database server. An IP or domain name

SITEINFO_DATABASE_USER

- Username to use for connecting to SITEINFO_DATABASE_HOST

SITEINFO_DATABASE_PASS

- Password to use for connecting to SITEINFO_DATABASE_HOST

Moodle Course Data
------------------

INSTALL_COURSE_FILE_PATH

- Absolute path on the server where moodle courses are stored

INSTALL_COURSE_WS_TOKEN

- Moodle plugin token string

INSTALL_COURSE_WS_FUNCTION

- Function to call on the moodle site

Google Auth
-----------

GOOGLE_CLIENT_ID

- Google ID with orvsd_central authentication enabled

GOOGLE_CLIENT_SECRET

- Google Secret

PROJECT_URI

- Authentication callback uri
