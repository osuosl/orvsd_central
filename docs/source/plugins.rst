Information About Plugins
=========================

.. There should be information about each of the plugins individually in this
   part of the documentation.

Git Branching Scheme
--------------------
ORVSD_Central's plugins are organized so that the main branches represent
either the development or production-ready version of the plugin for unique
versions of moodle.

For example, ``moodle_siteinfo``'s branching scheme looks like this::

      master
      moodle-1.9
      moodle-2.2
      moodle-2.5
      moodle-2.5_develop
      moodle-2.7_develop
      moodle-2.7_bug/<code.o.o issue #>
      moodle-2.7_feature/<title>

In this instance ``master`` stores all of the versions of the plugin while
``moodle-1.9``, ``moodle-2.2``, and ``moodle-2.5`` only hold the production
ready versions of the plugin for moodle 1.9, 2.2, and 2.5 respectively. Since
there is no production ready version of the plugin for moodle 2.7 there are
``moodle-2.7_develop``, ``moodle-2.7_bug/<code.o.o issue #>``, and 
``moodle-2.7_feature/<title>`` branches but no ``moodle-2.7`` yet. We also
still support moodle 2.5 so there is a develop branch for when improvements/ 
fixes need to be made.

