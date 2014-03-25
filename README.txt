Rename config.py.dist to config.py and change the
settings to match your database.

HOW TO do Migrations:

    If the db currently is not setup for migrations, ensure the SQLALCHEMY_MIGRATE_REPO in the config is correct, then run setup_db_migration.py.
    This will initialize the migration repo.
    Then to perform migrations, run db_migrate.py.  This will update the db based on information in models.py.

Running the server:

    Start by running:
        python manage.py initdb

    To start the server, run:
        python manage.py runserver -t <host> -p <port>

Tests:

    With the virtualenv activated run 'nosetests' in the top directory
    To create your own tests, subclass BaseTest
        from tests.mock_env import BaseTest
        class MyTests(BaseTest):
            ...
    If you need to override setUp, you'll need to call BaseTest's setUp as well
    with super
