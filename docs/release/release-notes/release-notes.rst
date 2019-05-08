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

This document compiles the release notes for the Hunter release of OPNFV Yardstick.


Version History
===============
+-------------------+-----------+---------------------------------+
| *Date*            | *Version* | *Comment*                       |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+
| May 10, 2019      | 8.0.0     | Yardstick for Hunter release    |
|                   |           |                                 |
+-------------------+-----------+---------------------------------+


Important Notes
===============

The software delivered in the OPNFV Yardstick_ Project, comprising the
*Yardstick framework*, and the *Yardstick test cases* is a realization of
the methodology in ETSI-ISG NFV-TST001_.

The *Yardstick* framework is *installer*, *infrastructure* and *application*
independent.

OPNFV Hunter Release
====================

This Hunter release provides *Yardstick* as a framework for NFVI testing
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

For Hunter release, the *Yardstick framework* is used for the following
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
| **Repo/tag**                   | yardstick/opnfv-8.0.0 |
|                                |                       |
+--------------------------------+-----------------------+
| **Yardstick Docker image tag** | opnfv-8.0.0           |
|                                |                       |
+--------------------------------+-----------------------+
| **Release designation**        | Hunter 8.0            |
|                                |                       |
+--------------------------------+-----------------------+
| **Release date**               | May 10, 2019          |
|                                |                       |
+--------------------------------+-----------------------+
| **Purpose of the delivery**    | OPNFV Hunter 8.0.0    |
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

 - The Yardstick Docker image: https://hub.docker.com/r/opnfv/yardstick (tag: opnfv-8.0.0)

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

+----------------+-------------------------------------------------------+
| **Runner**     | **Description**                                       |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *Arithmetic*   | Steps every run arithmetically according to specified |
|                | input value                                           |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *Duration*     | Runs for a specified period of time                   |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *Iteration*    | Runs for a specified number of iterations             |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *IterationIPC* | Runs a configurable number of times before it         |
|                | returns. Each iteration has a configurable timeout.   |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *Sequence*     | Selects input value to a scenario from an input file  |
|                | and runs all entries sequentially                     |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *Dynamictp*    | A runner that searches for the max throughput with    |
|                | binary search                                         |
|                |                                                       |
+----------------+-------------------------------------------------------+
| *Search*       | A runner that runs a specific time before it returns  |
|                |                                                       |
+----------------+-------------------------------------------------------+


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

.. note:: Yardstick Hunter 8.0.0 adds no new test cases.

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

- OpenStack Rocky


Document Version Changes
------------------------

This is the seventh tracked version of the Yardstick framework in OPNFV.
It includes the following documentation updates:

- Yardstick User Guide:
- Yardstick Developer Guide
- Yardstick Release Notes for Yardstick: this document


Feature additions
-----------------

- Add TRex Baremetal/SA scale up test cases.
- Add possibility to distribute DPDK/vhost-user ports/queues between CPU cores.
- Adding scale up test case for l3fwd OvS-DPDK.
- Add Testcase Prox Standalone SRIOV.
- Add vBNG PPPoE test cases functionality.
- Add IXIA Baremetal scale up testcases.
- Add vIPSEC testcases.
- Add TRex Baremetal/SA scale up test cases.
- Add OpenStack test cases with different framesize and IMIX.
- Add new scenario NSPerf-RFC3511.
- Add VPP traffic profiles for TRex traffic generator.
- Add Trex traffic generator to initate Traffic for VPP IPSEC.
- Add IxNextgen API for setting IP priority, flow tracking options, creating BGP protocol layer.
- Add Pktgen traffic generator for vCMTS.
- Add Trex traffic generator to initate Traffic for VPP IPSEC.
- Add sipp trafficgen based SampleVNFTrafficGen.
- Add ansible scripts to deploy Kubernetes.
- Update NSB report to use Barometer metrics.
- Support using existing private key when using external heat template file.

Scenario Matrix
===============


Test results
============

Test results are available in:

 - jenkins logs on CI: https://build.opnfv.org/ci/view/yardstick/


Known Issues/Faults
-------------------


Corrected Faults
----------------


Hunter 8.0.0 known restrictions/issues
======================================


Useful links
============

 - wiki project page: https://wiki.opnfv.org/display/yardstick/Yardstick

 - wiki Yardstick Hunter release planning page: https://wiki.opnfv.org/display/yardstick/Release+Hunter

 - Yardstick repo: https://git.opnfv.org/yardstick

 - Yardstick CI dashboard: https://build.opnfv.org/ci/view/yardstick

 - Yardstick grafana dashboard: http://testresults.opnfv.org/grafana/

 - Yardstick IRC channel: #opnfv-yardstick
