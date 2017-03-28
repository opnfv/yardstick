.. _yardstick-devguide:

.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*******************************
OPNFV YARDSTICK developer guide
*******************************


.. toctree::
   :numbered:
   :maxdepth: 2


============
Introduction
============

Yardstick is a project dealing with performance testing. Yardstick produces its
own test cases but can also be considered as a framework to support feature project testing.

Yardstick developed a test API that can be used by any OPNFV project. Therefore
there are many ways to contribute to Yardstick.

You can:

- Develop new test cases

- Review codes

- Develop Yardstick API / framework

- Develop Yardstick grafana dashboards and  Yardstick reporting page

- Write Yardstick documentation

This document describes how, as a developer, you may interact with the
Yardstick project. The first section details the main working areas of
the project. The Second part is a list of "How to" to help you to join
the Yardstick family whatever your field of interest is.


=========================
Yardstick developer areas
=========================


Yardstick framework
===================

Yardstick can be considered as a framework.
Yardstick is release as a docker file, including tools, scripts and a CLI
to prepare the environement and run tests.
It simplifies the integration of external test suites in CI pipeline
and provide commodity tools to collect and display results.

Since Danube, test categories also known as tiers have been created to
group similar tests, provide consistant sub-lists and at the end optimize
test duration for CI (see How To section).

The definition of the tiers has been agreed by the testing working group.

The tiers are:
  * smoke
  * features
  * components
  * performance
  * vnf


=======
How TOs
=======


How Yardstick works?
====================

The installation and configuration of the Yardstick is described in `[1]`_.
You can find notes on installing Yardstick with VM here `[2]`_.


How can I contribute to Yardstick?
==================================

If you are already a contributor of any OPNFV project, you can contribute to Yardstick.
If you are totally new to OPNFV, you must first create your Linux Foundation
account, then contact us in order to declare you in the repository database.

We distinguish 2 levels of contributors:

- The standard contributor can push patch and vote +1/0/-1 on any Yardstick patch
- The commitor can vote -2/-1/0/+1/+2 and merge

Yardstick commitors are promoted by the Yardstick contributors.


Gerrit & JIRA
=============

OPNFV uses Gerrit for web based code review and repository management for the Git Version Control System. You can access OPNFV Gerrit from `[3]`_.
Please note that you need to have Linux Foundation ID in order to use OPNFV Gerrit. You can get one from `[4]`_.
OPNFV uses JIRA for issue management. An important principle of change management is to have two-way trace-ability between issue management (i.e. JIRA) and the code repository (via Gerrit).
In this way, individual commits can be traced to JIRA issues and we also know which commits were used to resolve a JIRA issue.
If you want to contribute to Yardstick, you can pick a issue from Yardstick's JIRA dashboard or you can create you own issue and submit it to JIRA.


==========
References
==========

_`[1]`: http://artifacts.opnfv.org/yardstick/docs/userguide/index.html Yardstick user guide

_`[2]`: https://wiki.opnfv.org/display/yardstick/Notes+on+installing+Yardstick+with+VM Notes on installing Yardstick with VM

_`[3]`: http://gerrit.opnfv.org/ OPNFV gerrit

_`[4]`: https://identity.linuxfoundation.org/ Linux foundation
