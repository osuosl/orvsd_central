Configuration Options
=====================

General Project Options
-----------------------

PROJECT_PATH

- Project location used for migrations

PROJECT_LOGFILE

- Output file for the project's log statements

Flask
-----

DEBUG

- Enable debug output

SECRET_KEY:

- Flask session key

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

Google Auth
-----------

GOOGLE_CLIENT_ID

- Google ID with orvsd_central authentication enabled

GOOGLE_CLIENT_SECRET

- Google Secret

PROJECT_URI

- Authentication callback uri

Moodle Options (Services, Course locations, etc)
------------------------------------------------

MOODLE_SERVICES

- List of services ORVSD_Central will utilize for operating with moodle sites

INSTALL_COURSE_FILE_PATH

- Absolute path on the server where moodle courses are stored

INSTALL_COURSE_WS_TOKEN

- Token used by the orvsd_installcourse service
 - Deprication warning! - Moodle tokens will now be stored in the database

INSTALL_COURSE_WS_FUNCTION

- Function to call on the moodle site
 - Deprication warning! - MOODLE_SERVICES replaces this

INSTALL_COURSE_CATEGORY

- Category assigned to an installed course

INSTALL_COURSE_FIRSTNAME

- Moodle site administrator account info

INSTALL_COURSE_LASTNAME

- Moodle site administrator account info

INSTALL_COURSE_CITY

- Moodle site administrator account info

INSTALL_COURSE_EMAIL

- Moodle site administrator account info

INSTALL_COURSE_USERNAME

- Moodle site administrator account info

INSTALL_COURSE_PASS

- Moodle site administrator account info
