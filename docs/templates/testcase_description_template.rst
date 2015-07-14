.. NOTE::
   Template to be used for test case descriptions in Yardstick Project.
   Write one .rst per test case.
   Upload the .rst for the test case in /docs directory. Review in Gerrit.

******************
Test Case <slogan>
******************

.. contents:: Table of Contents
   :depth: 3

---------------------
Test Case Description
---------------------

Yardstick Test Case ID
----------------------

OPNFV_YARDSTICK_TC<abc>_<slogan>

where:
    - <abc>: check Jira issue for the test case
    - <slogan>: check Jira issue for the test case


Purpose
-------

Describe what is the purpose of the test case

Area
----

State the area and sub-area covered by the test case.

Areas: Compute, Networking, Storage

Sub-areas: Performance, System limit, QoS

Metrics
-------

What will be measured, attribute name or collection of attributes, behavior

References
----------

Reference documentation

--------------
Pre-requisites
--------------

Tools
-----

What tools are used to perform the measurements (e.g. fio, pktgen)


Configuration
-------------

State the .yaml file to use.

State default configuration in the tool(s) used to perform the measurements (e.g. fio, pktgen).

State what POD-specific configuration is required to enable running the test case in different PODs.

State SLA, if applicable.

State test duration.

-------
Results
-------

Expected outcome
----------------

State applicable graphical presentation

State applicable output details

State expected Value, behavior, pass/fail criteria



