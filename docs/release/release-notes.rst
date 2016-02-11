.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.


============================================
OPNFV Brahmaputra Release Note for Yardstick
============================================

.. toctree::
   :maxdepth: 2

.. _Yardstick: https://wiki.opnfv.org/yardstick

.. _Dashboard: http://130.211.154.108/grafana/dashboard/db/yardstick-main

.. _NFV-TST001: https://docbox.etsi.org/ISG/NFV/Open/Drafts/TST001_-_Pre-deployment_Validation/


Abstract
========

This document compiles the release notes for the OPNFV Brahmaputra release
for Yardstick framework as well as Yardstick_ Project deliverables.

License
=======

The *Yardstick framework*, the *Yardstick test cases* and the *ApexLake*
experimental framework are opensource software, licensed under the terms of the
Apache License, Version 2.0.


Version History
===============

+---------------+--------------------+---------------------------------+
| *Date*        | *Version*          | *Comment*                       |
|               |                    |                                 |
+---------------+--------------------+---------------------------------+
| Feb 25th,2016 |  1.0               | Brahmaputra release             |
|               |                    |                                 |
+---------------+--------------------+---------------------------------+


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

This Brahmaputra release provides *Yardstick* as a framework for NFVI testing
and OPNFV feature testing, automated in the OPNFV CI pipeline, including:

* Documentation generated with Sphinx

  * User Guide

  * Code Documentation

  * Release notes (this document)

  * Results

* Automated Yardstick test suite (daily, weekly)

  * Jenkins Jobs for OPNFV community labs

* Automated Yardstick test results visualization

  * Dashboard_ using Grafana (user:opnfv/password: opnfv), influxDB used as
    backend

* Yardstick framework source code

* Yardstick test cases yaml files

For Brahmaputra release, the *Yardstick framework* is used for the following
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

The *Yardstick framework* is developed in the OPNFV community, by the
Yardstick_ team.

.. note:: The test case description template used for the Yardstick test cases
  is based on the document ETSI-ISG NFV-TST001_; the results report template
  used for the Yardstick results is based on the IEEE Std 829-2008.


Release Data
============

+--------------------------------------+--------------------------------------+
| **Project**                          | Yardstick                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/tag**                         | yardstick/brahmaputra.1.0            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Yardstick Docker image tag**       | brahmaputra.1.0                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | Brahmaputra                          |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     | Feb 25th, 2016                       |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Brahmaputra release            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+


Version Change
--------------

Module Version Changes
~~~~~~~~~~~~~~~~~~~~~~

This is the first tracked release of Yardstick. It is based on following
upstream versions:

- OpenStack Liberty

- OpenDaylight Beryllium


Document Version Changes
~~~~~~~~~~~~~~~~~~~~~~~~

This is the first tracked version of the Yardstick framework in OPNFV.
It includes the following documentation:

- Yardstick User Guide

- Yardstick Code Documentation

- Yardstick Release Notes for Yardstick

- Test Results report for Brahmaputra testing with Yardstick


Reason for Version
------------------

Feature additions
~~~~~~~~~~~~~~~~~

This is the first tracked version of OPNFV Yardstick.


Corrected Faults
~~~~~~~~~~~~~~~~

This is the first tracked version of OPNFV Yardstick.


Known Faults
~~~~~~~~~~~~


+----------------------------+------------------------------------------------+
| **JIRA REFERENCE**         | **SLOGAN**                                     |
|                            |                                                |
+----------------------------+------------------------------------------------+
| JIRA: YARDSTICK-175        | Running test suite, if a test cases running    |
|                            | failed, the test is stopped.                   |
|                            |                                                |
+----------------------------+------------------------------------------------+
| JIRA: YARDSTICK-176        | Fix plotter bug since Output format has been   |
|                            | changed.                                       |
|                            |                                                |
+----------------------------+------------------------------------------------+
| JIRA: YARDSTICK-216        | ArgsAlreadyParsedError: arguments already      |
|                            | parsed: cannot register CLI option.            |
|                            |                                                |
+----------------------------+------------------------------------------------+

.. note:: The faults not related to *Yardstick* framework, addressing scenarios
  which were not fully verified, are listed in the OPNFV installer's release
  notes.


Deliverables
------------

Software Deliverables
~~~~~~~~~~~~~~~~~~~~~

**Yardstick framework source code <brahmaputra.1.0>**

+--------------------------------------+--------------------------------------+
| **Project**                          | Yardstick                            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Repo/tag**                         | yardstick/brahmaputra.1.0            |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Yardstick Docker image tag**       | brahmaputra.1.0                      |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release designation**              | Brahmaputra                          |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Release date**                     | Feb 25th, 2016                       |
|                                      |                                      |
+--------------------------------------+--------------------------------------+
| **Purpose of the delivery**          | OPNFV Brahmaputra release            |
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
|                     | * perf                                                |
|                     |                                                       |
|                     | * unixbench                                           |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Networking*        | * iperf3                                              |
|                     |                                                       |
|                     | * netperf                                             |
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
+---------------------+-------------------------------------------------------+
| *Parser*            | Tosca2Heat                                            |
|                     |                                                       |
+---------------------+-------------------------------------------------------+
| *Storage*           | fio                                                   |
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
|  influxdb                   | Post data to influxdB.                        |
|                             |                                               |
+-----------------------------+-----------------------------------------------+


Delivered Test cases
~~~~~~~~~~~~~~~~~~~~

* Generic NFVI test cases

  * OPNFV_YARDSTICK_TCOO1 - NW Performance

  * OPNFV_YARDSTICK_TCOO2 - NW Latency

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


* Test Cases for OPNFV HA Project:

  * OPNFV_YARDSTICK_TCO19 - HA: Control node Openstack service down

  * OPNFV_YARDSTICK_TC025 - HA: OpenStacK Controller Node abnormally down

* Test Case for OPNFV IPv6 Project:

  * OPNFV_YARDSTICK_TCO27 - IPv6 connectivity

* Test Case for OPNFV KVM Project:

  * OPNFV_YARDSTICK_TCO28 - KVM Latency measurements

* Test Case for OPNFV Parser Project:

  * OPNFV_YARDSTICK_TCO40 - Verify Parser Yang-to-Tosca
