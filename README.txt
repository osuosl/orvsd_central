Rename config.py.dist to config.py and change the
settings to match your database.

HOW TO do Migrations:

    If the db currently is not setup for migrations, ensure the SQLALCHEMY_MIGRATE_REPO in the config is correct, then run setup_db_migration.py.
    This will initialize the migration repo.
    Then to perform migrations, run db_migrate.py.  This will update the db based on information in models.py.

Running the server:

    Start by running:
        python manage.py initdb

    Currently there are two different ways to run the server (this will change very soon)
    One is with run.py:
        python run.py -i <host> -p <port>
    The other is with manage.py:
        python manage.py runserver -t <host> -p <port>

Tests:

    With the virtualenv activated run 'nosetests' in the top directory
