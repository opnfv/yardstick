=======
License
=======

OPNFV Fraser release note for Yardstick Docs
are licensed under a Creative Commons Attribution 4.0 International License.
You should have received a copy of the license along with this.
If not, see <http://creativecommons.org/licenses/by/4.0/>.

The *Yardstick framework*, the *Yardstick test cases* are open-source software,
 licensed under the terms of the Apache License, Version 2.0.

=======================================
OPNFV Fraser Release Note for Yardstick
=======================================

.. toctree::
   :maxdepth: 2

.. _Yardstick: https://wiki.opnfv.org/yardstick

.. _Dashboard: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main

.. _NFV-TST001: http://www.etsi.org/deliver/etsi_gs/NFV-TST/001_099/001/01.01.01_60/gs_NFV-TST001v010101p.pdf


Abstract
========

This document describes the release note of Yardstick project.


Version History
===============
+-------------------+-----------+---------------------------------+
| *Date*            | *Version* | *Comment*                       |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+
| April 27, 2018    | 6.0.0     | Yardstick for Fraser release    |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+


Important Notes
===============

The software delivered in the OPNFV Yardstick_ Project, comprising the
*Yardstick framework*, and the *Yardstick test cases* is a realization of
the methodology in ETSI-ISG NFV-TST001_.

The *Yardstick* framework is *installer*, *infrastructure* and *application*
independent.

OPNFV Fraser Release
====================

This Fraser release provides *Yardstick* as a framework for NFVI testing
and OPNFV feature testing, automated in the OPNFV CI pipeline, including:

* Documentation generated with Sphinx

  * User Guide
  * Developer Guide
  * Release notes (this document)
  * Results

* Automated Yardstick test suite (daily, weekly)

  * Jenkins Jobs for OPNFV community labs

* Automated Yardstick test results visualization

  * Dashboard_ using Grafana (user:opnfv/password: opnfv), influxDB is used as
    backend

* Yardstick framework source code

* Yardstick test cases yaml files

* Yardstick plug-in configuration yaml files, plug-in install/remove scripts

For Fraser release, the *Yardstick framework* is used for the following
testing:

* OPNFV platform testing - generic test cases to measure the categories:

  * Compute
  * Network
  * Storage

* OPNFV platform network service benchmarking (NSB)

  * NSB

* Test cases for the following OPNFV Projects:

  * Container4NFV
  * High Availability
  * IPv6
  * KVM
  * Parser
  * StorPerf
  * VSperf

The *Yardstick framework* is developed in the OPNFV community, by the
Yardstick_ team.

.. note:: The test case description template used for the Yardstick test cases
  is based on the document ETSI-ISG NFV-TST001_; the results report template
  used for the Yardstick results is based on the IEEE Std 829-2008.


Release Data
============

+--------------------------------+-----------------------+
| **Project**                    | Yardstick             |
|                                |                       |
+--------------------------------+-----------------------+
| **Repo/tag**                   | yardstick/opnfv-6.0.0 |
|                                |                       |
+--------------------------------+-----------------------+
| **Yardstick Docker image tag** | opnfv-6.0.0           |
|                                |                       |
+--------------------------------+-----------------------+
| **Release designation**        | Fraser                |
|                                |                       |
+--------------------------------+-----------------------+
| **Release date**               | April 27, 2018        |
|                                |                       |
+--------------------------------+-----------------------+
| **Purpose of the delivery**    | OPNFV Fraser 6.0.0    |
|                                |                       |
+--------------------------------+-----------------------+


Deliverables
============

Documents
---------

 - User Guide: http://docs.opnfv.org/en/stable-fraser/submodules/yardstick/docs/testing/user/userguide/index.html

 - Developer Guide: http://docs.opnfv.org/en/stable-fraser/submodules/yardstick/docs/testing/developer/devguide/index.html


Software Deliverables
---------------------

 - The Yardstick Docker image: https://hub.docker.com/r/opnfv/yardstick (tag: opnfv-6.0.0)

List of Contexts
^^^^^^^^^^^^^^^^

+--------------+-------------------------------------------+
| **Context**  | **Description**                           |
|              |                                           |
+--------------+-------------------------------------------+
| *Heat*       | Models orchestration using OpenStack Heat |
|              |                                           |
+--------------+-------------------------------------------+
| *Node*       | Models Baremetal, Controller, Compute     |
|              |                                           |
+--------------+-------------------------------------------+
| *Standalone* | Models VM running on Non-Managed NFVi     |
|              |                                           |
+--------------+-------------------------------------------+
| *Kubernetes* | Models VM running on Non-Managed NFVi     |
|              |                                           |
+--------------+-------------------------------------------+


List of Runners
^^^^^^^^^^^^^^^

Note: Yardstick Fraser 6.0.0 add two new Runners, "Dynamictp" and "Search".

+---------------+-------------------------------------------------------+
| **Runner**    | **Description**                                       |
|               |                                                       |
+---------------+-------------------------------------------------------+
| *Arithmetic*  | Steps every run arithmetically according to specified |
|               | input value                                           |
|               |                                                       |
+---------------+-------------------------------------------------------+
| *Duration*    | Runs for a specified period of time                   |
|               |                                                       |
+---------------+-------------------------------------------------------+
| *Iteration*   | Runs for a specified number of iterations             |
|               |                                                       |
+---------------+-------------------------------------------------------+
| *Sequence*    | Selects input value to a scenario from an input file  |
|               | and runs all entries sequentially                     |
|               |                                                       |
+---------------+-------------------------------------------------------+
| **Dynamictp** | A runner that searches for the max throughput with    |
|               | binary search                                         |
|               |                                                       |
+---------------+-------------------------------------------------------+
| **Search**    | A runner that runs a specific time before it returns  |
|               |                                                       |
+---------------+-------------------------------------------------------+


List of Scenarios
^^^^^^^^^^^^^^^^^

+----------------+-----------------------------------------------------+
| **Category**   | **Delivered**                                       |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *Availability* | Attacker:                                           |
|                |                                                     |
|                | * baremetal, process                                |
|                |                                                     |
|                | HA tools:                                           |
|                |                                                     |
|                | * check host, openstack, process, service           |
|                | * kill process                                      |
|                | * start/stop service                                |
|                |                                                     |
|                | Monitor:                                            |
|                |                                                     |
|                | * command, process                                  |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *Compute*      | * cpuload                                           |
|                | * cyclictest                                        |
|                | * lmbench                                           |
|                | * lmbench_cache                                     |
|                | * perf                                              |
|                | * unixbench                                         |
|                | * ramspeed                                          |
|                | * cachestat                                         |
|                | * memeoryload                                       |
|                | * computecapacity                                   |
|                | * SpecCPU2006                                       |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *Networking*   | * iperf3                                            |
|                | * netperf                                           |
|                | * netperf_node                                      |
|                | * ping                                              |
|                | * ping6                                             |
|                | * pktgen                                            |
|                | * sfc                                               |
|                | * sfc with tacker                                   |
|                | * networkcapacity                                   |
|                | * netutilization                                    |
|                | * nstat                                             |
|                | * pktgenDPDK                                        |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *Parser*       | Tosca2Heat                                          |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *Storage*      | * fio                                               |
|                | * bonnie++                                          |
|                | * storagecapacity                                   |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *StorPerf*     | storperf                                            |
|                |                                                     |
+----------------+-----------------------------------------------------+
| *NSB*          | vFW thoughput test case                             |
|                |                                                     |
+----------------+-----------------------------------------------------+


New Test cases
--------------

* Generic NFVI test cases

 * OPNFV_YARDSTICK_TCO84 - SPEC CPU 2006 for VM

* HA Test cases

 * OPNFV_YARDSTICK_TC087 - SDN Controller resilience in non-HA configuration
 * OPNFV_YARDSTICK_TC090 - Control node Openstack service down - database instance
 * OPNFV_YARDSTICK_TC091 - Control node Openstack service down - heat-api


Version Change
==============

Module Version Changes
----------------------

This is the sixth tracked release of Yardstick. It is based on following
upstream versions:

- OpenStack Pike
- OpenDayLight Oxygen


Document Version Changes
------------------------

This is the sixth tracked version of the Yardstick framework in OPNFV.
It includes the following documentation updates:

- Yardstick User Guide: add "network service benchmarking(NSB)" chapter;
  add "Yardstick - NSB Testing -Installation" chapter; add "Yardstick API" chapter;
  add "Yardstick user interface" chapter; Update Yardstick installation chapter;
- Yardstick Developer Guide
- Yardstick Release Notes for Yardstick: this document


Feature additions
-----------------

- Plugin-based test cases support Heat context
- SR-IOV support for the Heat context
- Support using existing network in Heat context
- Support running test cases with existing VNFs/without destroying VNF in Heat context
- Add vFW scale-up template
- Improvements of unit tests and gating
- GUI improvement about passing parameters


Scenario Matrix
===============

For Fraser 6.0.0, Yardstick was tested on the following scenarios:

+-------------------------+------+---------+----------+------+------+-------+
|        Scenario         | Apex | Compass | Fuel-arm | Fuel | Joid | Daisy |
+=========================+======+=========+==========+======+======+=======+
| os-nosdn-nofeature-noha |  X   |    X    |          |      |  X   |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-nofeature-ha   |  X   |    X    |    X     |  X   |  X   |   X   |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-bar-noha       |  X   |    X    |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-bar-ha         |  X   |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl-bgpvpn-ha        |  X   |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-calipso-noha   |  X   |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-kvm-ha         |      |    X    |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl_l3-nofeature-ha  |      |    X    |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl-sfc-ha           |      |    X    |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl-nofeature-ha     |      |         |          |  X   |      |   X   |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-ovs-ha         |      |         |          |  X   |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| k8-nosdn-nofeature-ha   |      |    X    |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| k8-nosdn-stor4nfv-noha  |      |    X    |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+


Test results
============

Test results are available in:

 - jenkins logs on CI: https://build.opnfv.org/ci/view/yardstick/

The reporting pages can be found at:

+---------------+----------------------------------------------------------------------------------+
| apex          | http://testresults.opnfv.org/reporting/fraser/yardstick/status-apex.html         |
+---------------+----------------------------------------------------------------------------------+
| compass       | http://testresults.opnfv.org/reporting/fraser/yardstick/status-compass.html      |
+---------------+----------------------------------------------------------------------------------+
| fuel\@x86     | http://testresults.opnfv.org/reporting/fraser/yardstick/status-fuel@x86.html     |
+---------------+----------------------------------------------------------------------------------+
| fuel\@aarch64 | http://testresults.opnfv.org/reporting/fraser/yardstick/status-fuel@aarch64.html |
+---------------+----------------------------------------------------------------------------------+
| joid          | http://testresults.opnfv.org/reporting/fraser/yardstick/status-joid.html         |
+---------------+----------------------------------------------------------------------------------+

Known Issues/Faults
-------------------


Corrected Faults
----------------

Fraser 6.0.0:

+--------------------+--------------------------------------------------------------------------+
| **JIRA REFERENCE** |                             **DESCRIPTION**                              |
+====================+==========================================================================+
|   YARDSTICK-831    | tc053 kill haproxy wrong                                                 |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-842    | load image fails when there's cirros image exist                         |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-857    | tc006 failed due to volume attached to different location "/dev/vdc"     |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-874    | Specify supported architecture for Ubuntu backports repository           |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-875    | Check if multiverse repository is available in Ubuntu                    |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-893    | Fix proxy env handling and ansible multinode support                     |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-899    | Variable local_iface_name is read before it is set                       |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-900    | Section in "upload_yardstick_image.yml" invalid                          |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-911    | Remove 'inconsistent-return-statements' from Pylint checks               |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-989    | Yardstick real-time influxdb KPI reporting regressions                   |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-994    | NSB set-up build script for baremetal broken                             |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-996    | Error in address input format in "_ip_range_action_partial"              |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1003   | Prox vnf descriptor cleanup for tg and vnf                               |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1006   | Ansible destroy script will fail if vm has already been undefined        |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1012   | constants: fix pylint warnings for OSError                               |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1014   | Remove unused args in                                                    |
|                    | network_services.traffic_profile.ixia_rfc2544.IXIARFC2544Profile         |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1016   | Allow vm to access outside world through default gateway                 |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1019   | For 'qemu-img version 2.10.1' unit 'MB' is not acceptable ansible script |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1021   | NSB: All Sample VNF test cases timeout after 1 hour of execution         |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1036   | Prox: Addition of storage of extra counters for Grafana                  |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1038   | Missing file which is described in the operation_conf.yaml               |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1047   | Error in string format in HeatTemplateError message                      |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1056   | yardstick report command print error when run test case                  |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1059   | Reduce the log level if TRex client is no connected                      |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1073   | Error when retrieving "options" section in "scenario"                    |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1080   | Running Test Case in Latest Yardstick Docker Image shows Error           |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1082   | tc043,tc055, tc063, tc075,  pass wrong node name in the ci scenario yaml |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1102   | Don't hide exception traceback from Task.start()                         |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1107   | bad exception traceback print due to atexit_handler                      |
+--------------------+--------------------------------------------------------------------------+
|   YARDSTICK-1120   | HA test case tc050 should start monitor before attack                    |
+--------------------+--------------------------------------------------------------------------+

Fraser 6.0.0 known restrictions/issues
======================================

+-----------+-----------+----------------------------------------------+
| Installer | Scenario  | Issue                                        |
+===========+===========+==============================================+
|           |           |                                              |
+-----------+-----------+----------------------------------------------+

Useful links
============

 - wiki project page: https://wiki.opnfv.org/display/yardstick/Yardstick

 - wiki Yardstick Fraser release planing page: https://wiki.opnfv.org/display/yardstick/Release+Fraser

 - Yardstick repo: https://git.opnfv.org/cgit/yardstick

 - Yardstick CI dashboard: https://build.opnfv.org/ci/view/yardstick

 - Yardstick grafana dashboard: http://testresults.opnfv.org/grafana/

 - Yardstick IRC chanel: #opnfv-yardstick
