.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

The *Yardstick framework*, the *Yardstick test cases* are open-source software,
 licensed under the terms of the Apache License, Version 2.0.

=======================
Yardstick Release Notes
=======================

.. toctree::
   :maxdepth: 2

.. _Yardstick: https://wiki.opnfv.org/display/yardstick

.. _Dashboard: http://testresults.opnfv.org/grafana/

.. _NFV-TST001: https://www.etsi.org/deliver/etsi_gs/NFV-TST/001_099/001/01.01.01_60/gs_NFV-TST001v010101p.pdf


Abstract
========

This document compiles the release notes for the Gambia release of OPNFV Yardstick.


Version History
===============
+-------------------+-----------+---------------------------------+
| *Date*            | *Version* | *Comment*                       |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+
| November 9, 2018  | 7.0.0     | Yardstick for Gambia release    |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+


Important Notes
===============

The software delivered in the OPNFV Yardstick_ Project, comprising the
*Yardstick framework*, and the *Yardstick test cases* is a realization of
the methodology in ETSI-ISG NFV-TST001_.

The *Yardstick* framework is *installer*, *infrastructure* and *application*
independent.

OPNFV Gambia Release
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

For Gambia release, the *Yardstick framework* is used for the following
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
| **Release designation**        | Gambia 7.0            |
|                                |                       |
+--------------------------------+-----------------------+
| **Release date**               | November 9, 2018      |
|                                |                       |
+--------------------------------+-----------------------+
| **Purpose of the delivery**    | OPNFV Gambia 7.0.0    |
|                                |                       |
+--------------------------------+-----------------------+


Deliverables
============

Documents
---------

 - User Guide: :ref:`<yardstick:userguide>`

 - Developer Guide: :ref:`<yardstick:devguide>`


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

.. note:: Yardstick Gambia 7.0.0 adds no new Runners.

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

.. note:: Yardstick Gambia 7.0.0 adds no new test cases.

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
- OpenDayLight Oxygen


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
- Agnostic VNF tests cases for reuse of standard RFC-2544 test case
- PROX enhancements and the addition of Standalone test case using SRIOV and
  OVS-DPDK
- Ixia enhancements for vBNG and PPPoE traffic
- Improvements of unit tests and gating


Scenario Matrix
===============

For Gambia 7.0.0, Yardstick was tested on the following scenarios:

+-------------------------+------+---------+----------+------+
|        Scenario         | Apex | Compass | Fuel-arm | Fuel |
+=========================+======+=========+==========+======+
| os-nosdn-nofeature-noha |   X  |         |          |      |
+-------------------------+------+---------+----------+------+
| os-nosdn-nofeature-ha   |   X  |         |          |      |
+-------------------------+------+---------+----------+------+
| os-odl-bgpvpn-noha      |   X  |         |          |      |
+-------------------------+------+---------+----------+------+
| os-nosdn-calipso-noha   |   X  |         |          |      |
+-------------------------+------+---------+----------+------+
| os-nosdn-kvm-ha         |      |    X    |          |      |
+-------------------------+------+---------+----------+------+
| os-odl-nofeature-ha     |      |         |     X    |   X  |
+-------------------------+------+---------+----------+------+
| os-odl-sfc-noha         |   X  |         |          |      |
+-------------------------+------+---------+----------+------+
| os-nosdn-ovs-ha         |      |         |          |   X  |
+-------------------------+------+---------+----------+------+
| k8-nosdn-nofeature-ha   |      |    X    |          |      |
+-------------------------+------+---------+----------+------+
| k8-nosdn-stor4nfv-noha  |      |    X    |          |      |
+-------------------------+------+---------+----------+------+
| k8-nosdn-stor4nfv-ha    |      |    X    |          |      |
+-------------------------+------+---------+----------+------+


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
| YARDSTICK-1389     | Add status filed for RFC2544 TC iterations                               |
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
| YARDSTICK-1462     | NSB: Add OvS 2.8.1 support in SA context                                 |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1492     | Make OvS server to listen on TCP                                         |
+--------------------+--------------------------------------------------------------------------+
| YARDSTICK-1493     | The RX queues number is hard-codded and cannot be changed                |
+--------------------+--------------------------------------------------------------------------+


Gambia 7.0.0 known restrictions/issues
======================================

+-----------+-----------+----------------------------------------------+
| Installer | Scenario  | Issue                                        |
+===========+===========+==============================================+
|           |           |                                              |
+-----------+-----------+----------------------------------------------+

Useful links
============

 - wiki project page: https://wiki.opnfv.org/display/yardstick/Yardstick

 - wiki Yardstick Gambia release planning page: https://wiki.opnfv.org/display/yardstick/Release+Gambia

 - Yardstick repo: https://git.opnfv.org/yardstick

 - Yardstick CI dashboard: https://build.opnfv.org/ci/view/yardstick

 - Yardstick grafana dashboard: http://testresults.opnfv.org/grafana/

 - Yardstick IRC channel: #opnfv-yardstick
