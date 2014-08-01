====
Setting up ORVSD Central
====
Pre-requisites:
----
You should have a database server running. for instructions on how to do this
take a look at *this* walkthrough.
.. *this* should like to an actual walkthrough on how to setup our database
    server either with Vagrant or TestKitchen.

Instructions
----
.. note:: You should have a virtualenv setup for this process.

1. After sourcing your virtualenv go to your directory which contains 
orvsd_central and run::
    
    pip install -r requirements.txt

.. if this is fixed this instruction should be removed
2. Next run the following command twice::
    
    python manage.py initdb

.. warning:: It won't work the first time. This command has to be run twice.

You will be prompted to create an account with certain credentials. Choose any
username, email, and password you wish.

3. Next::

    python manage.py import_data -d 
.. This instruction isn't complete until we find a way so the user doesn't need
    download the .csv file.

4. Finally::
    
    python manage.py gather

And there you have it! You've got an instance of ORVSD Central running.
Test it out by going to http://127.0.0.1:5000 in your browser
