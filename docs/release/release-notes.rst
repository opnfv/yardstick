.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.


============================================
OPNFV Colorado Release Note for Yardstick
============================================

.. toctree::
   :maxdepth: 2

.. _Yardstick: https://wiki.opnfv.org/yardstick

.. _Dashboard: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main

.. _NFV-TST001: http://www.etsi.org/deliver/etsi_gs/NFV-TST/001_099/001/01.01.01_60/gs_NFV-TST001v010101p.pdf


Abstract
========

This document describes the release note of Yardstick project.


License
=======

OPNFV Colorado release note for Yardstick Docs
are licensed under a Creative Commons Attribution 4.0 International License.
You should have received a copy of the license along with this.
If not, see <http://creativecommons.org/licenses/by/4.0/>.

The *Yardstick framework*, the *Yardstick test cases* and the *ApexLake*
experimental framework are opensource software, licensed under the terms of the
Apache License, Version 2.0.


Version History
===============

+----------------+--------------------+---------------------------------+
| *Date*         | *Version*          | *Comment*                       |
|                |                    |                                 |
+----------------+--------------------+---------------------------------+
| Aug 22nd, 2016 |  1.0               | Yardstick for Colorado release  |
|                |                    |                                 |
+----------------+--------------------+---------------------------------+


Important Notes
===============

The software delivered in the OPNFV Yardstick_ Project, comprising the
*Yardstick framework*, the *Yardstick test cases* and the experimental
framework *Apex Lake* is a realization of the methodology in ETSI-ISG
NFV-TST001_.

The *Yardstick* framework is *installer*, *infrastructure* and *application*
independent.


Summary
=======

This Colorado release provides *Yardstick* as a framework for NFVI testing
and OPNFV feature testing, automated in the OPNFV CI pipeline, including:

* Documentation generated with Sphinx

  * User Guide

  * Code Documentation

  * Release notes (this document)

  * Results

* Automated Yardstick test suite (daily, weekly)

  * Jenkins Jobs for OPNFV community labs

* Automated Yardstick test results visualization

  * Dashboard_ using Grafana (user:opnfv/password: opnfv), influxDB is used as
    backend

* Yardstick framework source code

* Yardstick test cases yaml files

* Yardstick pliug-in configration yaml files, plug-in install/remove scripts

For Colorado release, the *Yardstick framework* is used for the following
testing:

* OPNFV platform testing - generic test cases to measure the categories:

  * Compute

  * Network

  * Storage

* Test cases for the following OPNFV Projects:

  * High Availability

  * IPv6

  * KVM

  * Parser

  * StorPerf

  * VSperf

  * virtual Traffic Classifier

The *Yardstick framework* is developed in the OPNFV community, by the
Yardstick_ team. The *virtual Traffic Classifier* is a part of the Yardstick
Project.

.. note:: The test case description template used for the Yardstick test cases
  is based on the document ETSI-ISG NFV-TST001_; the results report template
  used for the Yardstick results is based on the IEEE Std 829-2008.


Release Data
============

+--------------------------------------+--------------------------------------+
| **Project**                          | Yardstick                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/tag**                         | yardstick/colorado.1.0               |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Yardstick Docker image tag**       | colorado.1.0                         |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | Colorado base release                |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     | September 22 2016                    |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | Colorado base release                |
|                                      |                                      |
+--------------------------------------+--------------------------------------+


Deliverables
============

Software Deliverables
---------------------

**Yardstick framework source code <colorado.1.0>**

+--------------------------------------+--------------------------------------+
| **Project**                          | Yardstick                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/tag**                         | yardstick/colorado.1.0               |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Yardstick Docker image tag**       | colorado.1.0                         |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | colorado                             |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     | September 22th, 2016                 |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Colorado release               |
|                                      |                                      |
+--------------------------------------+--------------------------------------+


**Contexts**

+---------------------+-------------------------------------------------------+
| **Context**         | **Description**                                       |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Heat*              | Models orchestration using OpenStack Heat             |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Node*              | Models Baremetal, Controller, Compute                 |
|                     |                                                       |
+---------------------+-------------------------------------------------------+


**Runners**

+---------------------+-------------------------------------------------------+
| **Runner**          | **Description**                                       |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Arithmetic*        | Steps every run arithmetically according to specified |
|                     | input value                                           |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Duration*          | Runs for a specified period of time                   |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Iteration*         | Runs for a specified number of iterations             |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Sequence*          | Selects input value to a scenario from an input file  |
|                     | and runs all entries sequentially                     |
|                     |                                                       |
+---------------------+-------------------------------------------------------+


**Scenarios**

+---------------------+-------------------------------------------------------+
| **Category**        | **Delivered**                                         |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Availability*      | Attacker:                                             |
|                     |                                                       |
|                     | * baremetal, process                                  |
|                     |                                                       |
|                     | HA tools:                                             |
|                     |                                                       |
|                     | * check host, openstack, process, service             |
|                     | * kill process                                        |
|                     | * start/stop service                                  |
|                     |                                                       |
|                     | Monitor:                                              |
|                     |                                                       |
|                     | * command, process                                    |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Compute*           | * cpuload                                             |
|                     |                                                       |
|                     | * cyclictest                                          |
|                     |                                                       |
|                     | * lmbench                                             |
|                     |                                                       |
|                     | * lmbench_cache                                       |
|                     |                                                       |
|                     | * perf                                                |
|                     |                                                       |
|                     | * unixbench                                           |
|                     |                                                       |
|                     | * ramspeed                                            |
|                     |                                                       |
|                     | * cachestat                                           |
|                     |                                                       |
|                     | * memeoryload                                         |
|                     |                                                       |
|                     | * computecapacity                                     |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Networking*        | * iperf3                                              |
|                     |                                                       |
|                     | * netperf                                             |
|                     |                                                       |
|                     | * netperf_node                                        |
|                     |                                                       |
|                     | * ping                                                |
|                     |                                                       |
|                     | * ping6                                               |
|                     |                                                       |
|                     | * pktgen                                              |
|                     |                                                       |
|                     | * sfc                                                 |
|                     |                                                       |
|                     | * sfc with tacker                                     |
|                     |                                                       |
|                     | * vtc instantion validation                           |
|                     |                                                       |
|                     | * vtc instantion validation with noisy neighbors      |
|                     |                                                       |
|                     | * vtc throughput                                      |
|                     |                                                       |
|                     | * vtc throughput in the presence of noisy neighbors   |
|                     |                                                       |
|                     | * networkcapacity                                     |
|                     |                                                       |
|                     | * netutilization                                      |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Parser*            | Tosca2Heat                                            |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Storage*           | fio                                                   |
|                     |                                                       |
|                     | storagecapacity                                       |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *StorPerf*          | storperf                                              |
|                     |                                                       |
+---------------------+-------------------------------------------------------+


**API to Other Frameworks**

+---------------------+-------------------------------------------------------+
| **Framework**       | **Description**                                       |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *ApexLake*          | Experimental framework that enables the user to       |
|                     | validate NFVI from the perspective of a VNF.          |
|                     | A virtual Traffic Classifier is utilized as VNF.      |
|                     | Enables experiments with SR-IOV on Compute Node.      |
|                     |                                                       |
+---------------------+-------------------------------------------------------+


**Test Results Output**

+-----------------------------+-----------------------------------------------+
| **Dispatcher**              | **Description**                               |
|                             |                                               |
+-----------------------------+-----------------------------------------------+
|  file                       | Log to a file.                                |
|                             |                                               |
+-----------------------------+-----------------------------------------------+
|  http                       | Post data to html.                            |
|                             |                                               |
+-----------------------------+-----------------------------------------------+
|  influxdb                   | Post data to influxDB.                        |
|                             |                                               |
+-----------------------------+-----------------------------------------------+


Delivered Test cases
--------------------

* Generic NFVI test cases

  * OPNFV_YARDSTICK_TCOO1 - NW Performance

  * OPNFV_YARDSTICK_TCOO2 - NW Latency

  * OPNFV_YARDSTICK_TCOO4 - Cache Utilization

  * OPNFV_YARDSTICK_TCOO5 - Storage Performance

  * OPNFV_YARDSTICK_TCOO8 - Packet Loss Extended Test

  * OPNFV_YARDSTICK_TCOO9 - Packet Loss

  * OPNFV_YARDSTICK_TCO10 - Memory Latency

  * OPNFV_YARDSTICK_TCO11 - Packet Delay Variation Between VMs

  * OPNFV_YARDSTICK_TCO12 - Memory Bandwidth

  * OPNFV_YARDSTICK_TCO14 - Processing Speed

  * OPNFV_YARDSTICK_TCO24 - CPU Load

  * OPNFV_YARDSTICK_TCO37 - Latency, CPU Load, Throughput, Packet Loss

  * OPNFV_YARDSTICK_TCO38 - Latency, CPU Load, Throughput, Packet Loss Extended
    Test

  * OPNFV_YARDSTICK_TCO42 - Network Performance

  * OPNFV_YARDSTICK_TCO43 - Network Latency Between NFVI Nodes

  * OPNFV_YARDSTICK_TCO44 - Memory Utilization

  * OPNFV_YARDSTICK_TCO55 - Compute Capacity

  * OPNFV_YARDSTICK_TCO61 - Network Utilization

  * OPNFV_YARDSTICK_TCO63 - Storage Capacity

  * OPNFV_YARDSTICK_TCO69 - Memory Bandwidth

  * OPNFV_YARDSTICK_TCO70 - Latency, Memory Utilization, Throughput, Packet
    Loss

  * OPNFV_YARDSTICK_TCO71 - Latency, Cache Utilization, Throughput, Packet Loss

  * OPNFV_YARDSTICK_TCO72 - Latency, Network Utilization, Throughput, Packet
    Loss

  * OPNFV_YARDSTICK_TC073 - Network Latency and Throughput Between Nodes

  * OPNFV_YARDSTICK_TCO75 - Network Capacity and Scale

* Test Cases for OPNFV HA Project:

  * OPNFV_YARDSTICK_TCO19 - HA: Control node Openstack service down

  * OPNFV_YARDSTICK_TC025 - HA: OpenStacK Controller Node abnormally down

  * OPNFV_YARDSTICK_TCO45 - HA: Control node Openstack service down - neutron
    server

  * OPNFV_YARDSTICK_TC046 - HA: Control node Openstack service down - keystone

  * OPNFV_YARDSTICK_TCO47 - HA: Control node Openstack service down - glance
    api

  * OPNFV_YARDSTICK_TC048 - HA: Control node Openstack service down - cinder
    api

  * OPNFV_YARDSTICK_TCO49 - HA: Control node Openstack service down - swift
    proxy

  * OPNFV_YARDSTICK_TC050 - HA: OpenStack Controller Node Network High
    Availability

  * OPNFV_YARDSTICK_TCO51 - HA: OpenStack Controller Node CPU Overload High
    Availability

  * OPNFV_YARDSTICK_TC052 - HA: OpenStack Controller Node Disk I/O Block High
    Availability

  * OPNFV_YARDSTICK_TCO53 - HA: OpenStack Controller Load Balance Service High
    Availability

  * OPNFV_YARDSTICK_TC054 - HA: OpenStack Virtual IP High Availability

* Test Case for OPNFV IPv6 Project:

  * OPNFV_YARDSTICK_TCO27 - IPv6 connectivity

* Test Case for OPNFV KVM Project:

  * OPNFV_YARDSTICK_TCO28 - KVM Latency measurements

* Test Case for OPNFV Parser Project:

  * OPNFV_YARDSTICK_TCO40 - Verify Parser Yang-to-Tosca

* Test Case for OPNFV StorPerf Project:

  * OPNFV_YARDSTICK_TCO74 - Storperf

* Test Cases for Virtual Traffic Classifier:

  * OPNFV_YARDSTICK_TC006 - Virtual Traffic Classifier Data Plane Throughput
Benchmarking Test

  * OPNFV_YARDSTICK_TC007 - Virtual Traffic Classifier Data Plane Throughput
Benchmarking in presence of noisy neighbors Test

  * OPNFV_YARDSTICK_TC020 - Virtual Traffic Classifier Instantiation Test

  * OPNFV_YARDSTICK_TC021 - Virtual Traffic Classifier Instantiation in
presence of noisy neighbors Test


Version Change
==============

Module Version Changes
----------------------

This is the third tracked release of Yardstick. It is based on following
upstream versions:

- OpenStack Mitaka

- OpenDaylight Beryllium


Document Version Changes
------------------------

This is the first tracked version of the Yardstick framework in OPNFV.
It includes the following documentation updates:

- Yardstick User Guide: added yardstick plugin chapter; added Store Other
Project's Test Results in InfluxDB chapter; Refine yardstick instantion chapter.

- Yardstick Code Documentation: no changes

- Yardstick Release Notes for Yardstick: this document

- Test Results report for Colorado testing with Yardstick: updated listed of
verified scenarios and limitations


Reason for Version
==================
* TODO *

Feature additions
-----------------
* TODO *

Corrected Faults
----------------
* TODO *

Known Issues/Faults
------------
 - IPv6 support
 - Boot up VM failed in joid-os-nosdn-lxd-ha and joid-os-nosdn-lxd-noha scenarios
 - Yardstick CI job timeout in fuel-os-onos-nofeature-ha scenario
 - SSH timeout in apex-os-onos-sfc-ha, apex-os-onos-nofeature-ha and apex-os-odl_l3-nofeature-ha scenarios
 - Scp /home/stack/overcloudrc failed in apex-os-nosdn-ovs-noha and apex-os-odl_l2-sfc-noha scenarios

.. note:: The faults not related to *Yardstick* framework, addressing scenarios
  which were not fully verified, are listed in the OPNFV installer's release
  notes.


Colorado known restrictions/issues
==================================
+-----------+-----------+----------------------------------------------+
| Installer | Scenario  |  Issue                                       |
+===========+===========+==============================================+
| any       | *-bgpvpn  | floating ips not supported. Some Test cases  |
|           |           | related to floating ips are excluded.        |
+-----------+-----------+----------------------------------------------+
* TODO *


Test results
============

Test results are available in:

 - jenkins logs on CI: https://build.opnfv.org/ci/view/yardstick/


Open JIRA tickets
=================

+------------------+-----------------------------------------------+
|   JIRA           |         Description                           |
+==================+===============================================+
+------------------+-----------------------------------------------+
+------------------+-----------------------------------------------+
+------------------+-----------------------------------------------+
+------------------+-----------------------------------------------+
+------------------+-----------------------------------------------+


Useful links
============

 - wiki project page: https://wiki.opnfv.org/display/yardstick/Yardstick

 - wiki Yardstick Colorado release planing page: https://wiki.opnfv.org/display/yardstick/Yardstick+Colorado+Release+Planning

 - wiki Yardstick Colorado release jira page: https://wiki.opnfv.org/display/yardstick/Jira+Yardstick-Colorado

 - Yardstick repo: https://git.opnfv.org/cgit/yardstick

 - Yardstick CI dashboard: https://build.opnfv.org/ci/view/yardstick

 - Yardstick grafana dashboard: http://testresults.opnfv.org/grafana/

 - Yardstick IRC chanel: #opnfv-yardstick

