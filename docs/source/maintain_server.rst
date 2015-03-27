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

When you need to change the schema (change the name of a column, table, modify a table or data),
you will need to generate a migration file and then edit it. Check out some examples in the
migrations folder. Some things
that will not require a migration are changes to methods within the models.py classes which use the
data but do not necessarily represent the data. Take the method **User.get_id(self)**. changing this
method to **return unicode(self.id)** instead of a typo you found such as: **return unicode(self.od)**
will not require a migration because the column is not changed, but rather code that references
the column.

Run this command from the orvsd_central folder when you are ready to generate the revision
files that you will modify to do the actual migration.

    PYTHONPATH='.' alembic revision -m "my nifty changes"
    
Now that the revision exists, go to the migrations folder and fill out the function stubs which
only have "pass" as their body. The migrations that you write will need to only modify the table
and any data that is needed. Seperate changes will need to be made by the actual orvsd code
that should be changed as a result of the new schema. Once this is complete we can run the migration.

To run a migration, from the orvsd_central folder, run:

    PYTHONPATH='.' alembic upgrade head

A migration will take place if any are needed, else alembic might inform you of
already being up to date.
