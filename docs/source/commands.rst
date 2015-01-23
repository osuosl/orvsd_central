manage.py Commands
==================

The following are commands available from manage.py

import_data
-----------

Description: Imports District and School info for the state of Oregon

Pre-reqs: A a csv (one is provided in orvsd_central/config/*.csv)

The current format of this csv is:
    District State ID, District, School State ID, School, County

Options: -d <file name>, --data <file name>

manage.py has a top level option -c '/path/to/config' for when you choose to
use a defferent config than config/default.py

run_server
----------

Runs the orvsd_central server

Options:
    - -t <IP Address> - server listening address
    - -p <Port> - Port Number to listen on

gather_tokens
-------------

Gathers tokens from all moodle sites in ORVSD Central's database. The tokens
are for services listed in the MOODLE_SERVICES configuration option. Each
listed service must be the shortname of a plugin.

Options: None

setup_db
--------

Initialize the database or keep the schema up to date with migrations

Options: None
