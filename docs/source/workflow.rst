Development Workflow
====================

When developing ORVSD Central please follow this general workflow.

General Workflow Guidelines
---------------------------

1. Create Issues

    * When an issue arises, create a GitHub issue to fix it. 
    * When a feature needs to be developed, create an issue for that as well.
    * Do not work on anything that will eventually be pushed to production,
      unless an issue exists for that task.

2. Make Branches for each issue you work on
    
    * Unless expressly specified, one should always branch from `develop` on
      ORVSD Central.
    * When creating a new branch in the orvsd_central repo please follow `these
      guidelines <./branching.html>`_. [descriptive_name-<issue #>]
    * Refer to `these docs <./plugins.html>`_ for specific branching syntax with 
      plugins. `[<moodle version>/<feature or bug>/<issue #>_optional_descriptive_name]`
    * Only after you have created an issue on either GitHub or Code.O.O for 
      ORVSD Central or the Moodle Plugins respectively work can begin on that 
      issue.

3. Assign individuals to each issue

    * Once you have created an issue make sure to assign it to one of the
      developers on the project who can best resolve the issue. If you yourself
      can handle the issue assign yourself. The goal is to have every issue
      assigned and accounted for.
    * If you don't know who best to take on the task assign it to yourself or
      check with the development staff to who is available to take the issue.
    * Contact whoever you have assigned to the issue in the dev irc channel so
      they know they have been assigned said issue; otherwise it may never get
      done and nobody wants that to happen.
      

4. Review regularly

    * Projects should be reviewed from the planning stages onward 
    * Before beginning a task be sure to have your plan reviewed by the one
      of your peers.
    * Throughout your development make sure your progress and plans are being
      assessed by your peers, especially if they are changing frequently.

5. Designing/Testing/Reviewing

    When developing follow these steps:

    A. Draft a design
    B. Review the design
    C. Get the design approved
    D. Write tests
    E. Get tests approved
    F. Implement the approved design
    G. Review implementation
    H. Review code before anything gets merged
