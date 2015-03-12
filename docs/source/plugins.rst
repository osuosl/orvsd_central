Information About Plugins
=========================

Moodle Plugins
--------------
ORVSD_Central currently has three moodle plugins/webservices which it uses to
install courses and get site-info. Create_Course is a webservice while 
Site_Info is a regular plugin currently in development to become a
webservice.

.. TODO There should be information about each of the plugins individually in 
   this part of the documentation.

Git Branching Scheme
--------------------
ORVSD_Central's Moodle plugins are organized so that branches represent either 
the development, production-ready, feature-development, or bug-fix versions of 
the plugin for unique versions of moodle.

For example, ``moodle_siteinfo``'s branching scheme looks like this::

      master
      moodle-1.9
      moodle-2.2
      moodle-2.5
      moodle-2.5_develop
      moodle-2.7_develop
      moodle-2.7/bug/<issue #>_optional_descriptive_name
      moodle-2.7/feature/<issue #>_optional_descriptive_name

In this instance ``master`` stores all of the versions of the plugin while
``moodle-1.9``, ``moodle-2.2``, and ``moodle-2.5`` hold the production-ready 
versions of the plugin for moodle 1.9, 2.2, and 2.5 respectively. Since there 
is no production ready version of the plugin for moodle 2.7 there are 
``moodle-2.7_develop``, ``moodle-2.7/bug/<issue #>_optional_descriptive_name``,
and ``moodle-2.7/feature/<issue #>_optional_descriptive_name`` branches but no 
``moodle-2.7`` yet. We also still support moodle 2.5 so there is a develop 
branch for when improvements/fixes need to be made.

Moving forward there will be a ``moodle-2.7`` branch, which will contain the 
production-ready version of the plugin which works with moodle 2.7. During the 
next upgrade, to moodle 2.9 for example, there will be a branch off of
``moodle-2.7`` called ``moodle-2.9_develop`` where any compatibility changes
and bug fixes will happen. Once that version of the plugin is ready for
production a ``moodle-2.9`` branch will be made off of ``moodle-2.9_develop``. 
Any further fixes to the plugin will happen in 
``moodle-2.9_bug/<issue#>_optional_descriptive_name`` and pulled into 
``moodle-2.9``.

The ``master`` branch is not used in this workflow and is only there for 
posterity.
