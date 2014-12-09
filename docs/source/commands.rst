manage.py Commands
==================

The following are commands available from manage.py

import_data
-----------

Description: Imports District and School info for the state of Oregon

Pre-reqs: A a csv located at https://docs.google.com/a/osuosl.org/spreadsheet/ccc?key=0AkqubyBcoQy7dHB5WlhNNzI3SXg1MWQ0LVdSNnhMMVE&usp=drive_web#gid=0

The current format of this csv is:
    District State ID, District, School State ID, School, County

Options: -d <file name>

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

Gathers tokens from moodle sites. The tokens are for services listed in the
MOODLE_SERVICES configuration option

Options: None

initdb
------

Initializes the database configured in your config. This is typically only ran
during the setup phase

Options: None
