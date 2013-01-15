Rename config.py.dist to config.py and change the
settings to match your database.

HOW TO do Migrations:

    If the db currently is not setup for migrations, ensure the SQLALCHEMY_MIGRATE_REPO in the config is correct, then run setup_db_migration.py.
    This will initialize the migration repo.
    Then to perform migrations, run db_migrate.py.  This will update the db based on information in models.py.
