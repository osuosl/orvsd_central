Maintain a Server
=================

Migrations
----------

Once in a while a database migration will need to be applied. What is migration
you ask? A migration is a simple (or not so simple) modification to the
structure of the database, not necessarily to the data, though that can occur
as well. The point of migrations is *never* to destroy data, simply modify how
it is stored.

We use a nifty little tool called alembic to handle database versioning for us.
To run a migration, from the orvsd_central folder, run:

    PYTHONPATH='.' alembic upgrade head

A migration will take place if any are needed, else alembic might inform you of
already being up to date.
