=======
License
=======

OPNFV Gambia release notes for Yardstick Docs
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

This document describes the release notes of Yardstick project.


Version History
===============
+-------------------+-----------+---------------------------------+
| *Date*            | *Version* | *Comment*                       |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+
| November 2, 2018  | 7.0.0     | Yardstick for Gambia release    |
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

This Gambia release provides *Yardstick* as a framework for NFVI testing
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
| **Repo/tag**                   | yardstick/opnfv-7.0.0 |
|                                |                       |
+--------------------------------+-----------------------+
| **Yardstick Docker image tag** | opnfv-7.0.0           |
|                                |                       |
+--------------------------------+-----------------------+
| **Release designation**        | Gambia                |
|                                |                       |
+--------------------------------+-----------------------+
| **Release date**               | Nov 02, 2018          |
|                                |                       |
+--------------------------------+-----------------------+
| **Purpose of the delivery**    | OPNFV Gambia 7.0.0    |
|                                |                       |
+--------------------------------+-----------------------+


Deliverables
============

Documents
---------

 - User Guide: http://docs.opnfv.org/en/stable-gambia/submodules/yardstick/docs/testing/user/userguide/index.html

 - Developer Guide: http://docs.opnfv.org/en/stable-gambia/submodules/yardstick/docs/testing/developer/devguide/index.html


Software Deliverables
---------------------

 - The Yardstick Docker image: https://hub.docker.com/r/opnfv/yardstick (tag: opnfv-7.0.0)

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

.. note:: Yardstick Fraser 7.0.0 add xx new Runners, .

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
| *Dynamictp*   | A runner that searches for the max throughput with    |
|               | binary search                                         |
|               |                                                       |
+---------------+-------------------------------------------------------+
| *Search*      | A runner that runs a specific time before it returns  |
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

.. note:: Yardstick Gambia 7.0.0 added xxx new test cases.

* Generic NFVI test cases

 * (e.g.) OPNFV_YARDSTICK_TCO84 - SPEC CPU 2006 for VM

* HA Test cases

 * (e.g.) OPNFV_YARDSTICK_TC093 - SDN Vswitch resilience in non-HA or HA configuration


Version Change
==============

Module Version Changes
----------------------

This is the seventh tracked release of Yardstick. It is based on following
upstream versions:

- OpenStack Queens

.. TODO: Check ODL version

- OpenDayLight Oxygen(?)


Document Version Changes
------------------------

This is the seventh tracked version of the Yardstick framework in OPNFV.
It includes the following documentation updates:

- Yardstick User Guide:

  - Remove vTC chapter;

- Yardstick Developer Guide
- Yardstick Release Notes for Yardstick: this document


Feature additions
-----------------

- Simplify Yardstick installation to use a single ansible playbook (nsb_setup.yaml)
- Spirent support
- vEPC testcases
- Improvements of unit tests and gating


Scenario Matrix
===============

For Gambia 7.0.0, Yardstick was tested on the following scenarios:

+-------------------------+------+---------+----------+------+------+-------+
|        Scenario         | Apex | Compass | Fuel-arm | Fuel | Joid | Daisy |
+=========================+======+=========+==========+======+======+=======+
| os-nosdn-nofeature-noha |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-nofeature-ha   |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-bar-noha       |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-bar-ha         |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl-bgpvpn-ha        |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-calipso-noha   |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-kvm-ha         |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl_l3-nofeature-ha  |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl-sfc-ha           |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-odl-nofeature-ha     |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| os-nosdn-ovs-ha         |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| k8-nosdn-nofeature-ha   |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+
| k8-nosdn-stor4nfv-noha  |      |         |          |      |      |       |
+-------------------------+------+---------+----------+------+------+-------+


Test results
============

Test results are available in:

 - jenkins logs on CI: https://build.opnfv.org/ci/view/yardstick/

The reporting pages can be found at:

+---------------+----------------------------------------------------------------------------------+
| apex          | http://testresults.opnfv.org/reporting/gambia/yardstick/status-apex.html         |
+---------------+----------------------------------------------------------------------------------+
| compass       | http://testresults.opnfv.org/reporting/gambia/yardstick/status-compass.html      |
+---------------+----------------------------------------------------------------------------------+
| fuel\@x86     | http://testresults.opnfv.org/reporting/gambia/yardstick/status-fuel@x86.html     |
+---------------+----------------------------------------------------------------------------------+
| fuel\@aarch64 | http://testresults.opnfv.org/reporting/gambia/yardstick/status-fuel@aarch64.html |
+---------------+----------------------------------------------------------------------------------+
| joid          | http://testresults.opnfv.org/reporting/gambia/yardstick/status-joid.html         |
+---------------+----------------------------------------------------------------------------------+

Known Issues/Faults
-------------------


Corrected Faults
----------------

Gambia 7.0.0:

+--------------------+--------------------------------------------------------------------------+
| **JIRA REFERENCE** |                             **DESCRIPTION**                              |
+====================+==========================================================================+
| YARDSTICK-1137     | Fix CLI argument handling in nsb_setup.sh                                |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1220     | Get stats for multiple port simultaneously                               |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1260     | Added missing functionality to start VM and access it using SSH keys     |
|                    | in Standalone contexts.                                                  |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1298     | Allows for in-line overriding/modification of traffic profile variables  |
|                    | from the testcase file.                                                  |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1368     | Updated existing test cases in Yardstick to minimize changes done        |
|                    | manually to run standalone tests for Trex.                               |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1395     | Update 'configure_uwsgi' role to work in baremetal/container modes.      |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1402     | Change IP assignment for VM to static for standalone context             |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1404     | CPU Utilization for VNF and traffic generator are now graphed on Grafana |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1411     | Fix Yardstick Docker image ARM build                                     |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1414     | Update the pinned sampleVNF version to use a commit instead of a branch  |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1418     | NSB PROX NFVi test now stops after reaching expected precision           |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1457     | Fix influxdb "field type conflict" error                                 |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1458     | Update Grafana to display "real-time" data instead of historical data.   |
+--------------------+--------------------------------------------------------------------------+


Fraser 7.0.0 known restrictions/issues
======================================

+-----------+-----------+----------------------------------------------+
| Installer | Scenario  | Issue                                        |
+===========+===========+==============================================+
|           |           |                                              |
+-----------+-----------+----------------------------------------------+

Useful links
============

 - wiki project page: https://wiki.opnfv.org/display/yardstick/Yardstick

 - wiki Yardstick Fraser release planning page: https://wiki.opnfv.org/display/yardstick/Release+Gambia

 - Yardstick repo: https://git.opnfv.org/cgit/yardstick

 - Yardstick CI dashboard: https://build.opnfv.org/ci/view/yardstick

 - Yardstick grafana dashboard: http://testresults.opnfv.org/grafana/

 - Yardstick IRC channel: #opnfv-yardstick
