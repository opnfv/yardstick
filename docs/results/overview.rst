.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

=====================
Yardstick Test Report
=====================

.. toctree::
   :maxdepth: 2

Introduction
============

Document Identifier
-------------------

This document is part of deliverables of the OPNFV release brahmaputra.1.0

Scope
-----

.. _Dashboard: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _Jenkins: https://build.opnfv.org/ci/view/yardstick/
.. _Scenarios: http://130.211.154.108/grafana/dashboard/db/yardstick-scenarios

This document provides an overview of the results of test cases developed by
the OPNFV Yardstick Project, executed on OPNFV community labs.

OPNFV Continous Integration provides automated build, deploy and testing for
the software developed in OPNFV. Unless stated, the reported tests are
automated via Jenkins Jobs.

Test results are visible in the following dashboard:

* *Yardstick* Dashboard_:  uses influx DB to store test results and Grafana for
   visualization (user: opnfv/ password: opnfv)


References
----------

* IEEE Std 829-2008. "Standard for Software and System Test Documentation".

* OPNFV Brahamputra release note for Yardstick.



General
=======

Yardstick Test Cases have been executed for scenarios and features defined in
this OPNFV release.

The test environments were installed by one of the following: Apex, Compass,
Fuel or Joid; one single installer per POD.

The results of executed tests are available in Dashboard_ and all logs stored
in Jenkins_.

After one week of measurments, in general, SDN ONOS showed lower latency than
SDN ODL, which showed lower latency than an environment installed with pure
OpenStack. Additional time and PODs make this a non-conclusive statement, see
Scenarios_ for a snapshot and Dashboard_ for complete results.

It was not possible to execute the entire Yardstick test cases suite on the
PODs assigned for release verification over a longer period of time, due to
continuous work on the software components and blocking faults either on
environment, feature or test framework.

Four consecutive successful runs was defined as criteria for release.
It is a recommendation to run Yardstick test cases over a longer period
of time in order to better understand the behavior of the system.



Document change procedures and history
--------------------------------------

+--------------------------------------+--------------------------------------+
| **Project**                          | Yardstick                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/tag**                         | yardstick/brahmaputra.1.0            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | Brahmaputra                          |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     | Feb 25th, 2016                       |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Brahmaputra release test       |
|                                      | results.                             |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
