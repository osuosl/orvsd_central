.. ORVSD Central documentation master file, created by
   sphinx-quickstart on Mon Apr 15 16:24:14 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

About ORVSD Central
=========================================

.. toctree::
   :maxdepth: 2

   orvsd_central

Who
------------------------


Functionality
------------------------
Register: There is not a link to this page, but you must be an admin to register new users.
          The url is /register.

Report: Main page for reporting statistics we've gathered about all the
        moodle/drupal sites we host, how many students they have, and which 
        districts have which schools.
        Active districts: districts that have a non-zero amount of users within
                          the schools that reside in them.
        Inactive districts: districts with schools that have zero users.

        Inside of each district, you can click a school and see the info for the
        sites that reside in each of those schools.

Update Available Courses: Searches the course directory (as designated in the config)
                          for directories and the courses that reside in them, then
                          use the metadata from those courses to generate course and
                          course_detail objects to refer to them.

Install Course: Allows you to install multiple courses to multiple sites and filter by the
                folder they reside in.

Add/Modify/Delete: Add/Modify/Delete objects of any Model type we have created.
                   WARNING: If you try and do this with the 'Users' category,
                            the hashed password will be overwritten by the plaintext
                            '********' that currently replaces the password so we
                            don't send it back to the client.


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

