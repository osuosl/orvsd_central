from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from config import DATABASE_TYPE 
from orvsd_central import db
import os.path

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    print "Creating Repository for Migrations..."
    api.create(SQLALCHEMY_MIGRATE_REPO, DATABASE_TYPE)
    print "Configuring Version Control..."
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

else:
    print "Configuring Version Control..."
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
