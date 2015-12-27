===========
Methodology
===========

Abstract
========

This chapter describes the methodology implemented by the Yardstick project for
verifying the NFV Infrastructure from the perspective of a VNF.

ETSI-NFV
========

.. _NFV-TST001: https://docbox.etsi.org/ISG/NFV/Open/Drafts/TST001_-_Pre-deployment_Validation/

The document ETSI GS NFV-TST001_, "Pre-deployment Testing; Report on Validation
of NFV Environments and Services", recommends methods for pre-deployment
testing of the functional components of an NFV environment.

The Yardstick project implements the methodology described in chapter 6, "Pre-
deployment validation of NFV infrastructure".

The methodology consists in decomposing the typical VNF work-load performance
metrics into a number of characteristics/performance vectors, which each can be
represented by distinct test-cases.

The methodology includes five steps:

* *Step1:* Define Infrastruture - the HW, SW and corresponding configuration
   target for validation; the OPNFV infrastructure, in OPNFV community labs.

* *Step2:* Identify VNF type - the application for which the infrastructure is
   to be validated, and its requirements on the underlying infrastructure.

* *Step3:* Select test cases - depending on the workload that represents the
   application for which the infrastruture is to be validated, the relevant
   test cases amongst the list of available Yardstick test cases.

* *Step4:* Execute tests - define the duration and number of iterations for the
   selected test cases, tests runs are automated via OPNFV Jenkins Jobs.

* *Step5:* Collect results - using the common API for result collection.

Metrics
=======

The metrics, as defined by ETSI GS NFV-TST001, are shown in
:ref:`Table1 <table2_1>`, :ref:`Table2 <table2_2>` and
:ref:`Table3 <table2_3>`.

In OPNFV Brahmaputra release, generic test cases covering aspects of the listed
metrics are available; further OPNFV releases will provide extended testing of
these metrics.
The view of available Yardstick test cases cross ETSI definitions in
:ref:`Table1 <table2_1>`, :ref:`Table2 <table2_2>` and :ref:`Table3 <table2_3>`
is shown in :ref:`Table4 <table2_4>`.
It shall be noticed that the Yardstick test cases are examples, the test
duration and number of iterations are configurable, as are the System Under
Test (SUT) and the attributes (or, in Yardstick nomemclature, the scenario
options).

.. _table2_1:

**Table 1 - Performance/Speed Metrics**

+---------+-------------------------------------------------------------------+
| Category| Performance/Speed                                                 |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Compute | * Latency for random memory access                                |
|         | * Latency for cache read/write operations                         |
|         | * Processing speed (instructions per second)                      |
|         | * Throughput for random memory access (bytes per second)          |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Network | * Throughput per NFVI node (frames/byte per second)               |
|         | * Throughput provided to a VM (frames/byte per second)            |
|         | * Latency per traffic flow                                        |
|         | * Latency between VMs                                             |
|         | * Latency between NFVI nodes                                      |
|         | * Packet delay variation (jitter) between VMs                     |
|         | * Packet delay variation (jitter) between NFVI nodes              |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Storage | * Sequential read/write IOPS                                      |
|         | * Random read/write IOPS                                          |
|         | * Latency for storage read/write operations                       |
|         | * Throughput for storage read/write operations                    |
|         |                                                                   |
+---------+-------------------------------------------------------------------+

.. _table2_2:

**Table 2 - Capacity/Scale Metrics**

+---------+-------------------------------------------------------------------+
| Category| Capacity/Scale                                                    |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Compute | * Number of cores and threads- Available memory size              |
|         | * Cache size                                                      |
|         | * Processor utilization (max, average, standard deviation)        |
|         | * Memory utilization (max, average, standard deviation)           |
|         | * Cache utilization (max, average, standard deviation)            |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Network | * Number of connections                                           |
|         | * Number of frames sent/received                                  |
|         | * Maximum throughput between VMs (frames/byte per second)         |
|         | * Maximum throughput between NFVI nodes (frames/byte per second)  |
|         | * Network utilization (max, average, standard deviation)          |
|         | * Number of traffic flows                                         |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Storage | * Storage/Disk size                                               |
|         | * Capacity allocation (block-based, object-based)                 |
|         | * Block size                                                      |
|         | * Maximum sequential read/write IOPS                              |
|         | * Maximum random read/write IOPS                                  |
|         | * Disk utilization (max, average, standard deviation)             |
|         |                                                                   |
+---------+-------------------------------------------------------------------+

.. _table2_3:

**Table 3 - Availability/Reliability Metrics**

+---------+-------------------------------------------------------------------+
| Category| Availability/Reliability                                          |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Compute | * Processor availability (Error free processing time)             |
|         | * Memory availability (Error free memory time)                    |
|         | * Processor mean-time-to-failure                                  |
|         | * Memory mean-time-to-failure                                     |
|         | * Number of processing faults per second                          |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Network | * NIC availability (Error free connection time)                   |
|         | * Link availability (Error free transmission time)                |
|         | * NIC mean-time-to-failure                                        |
|         | * Network timeout duration due to link failure                    |
|         | * Frame loss rate                                                 |
|         |                                                                   |
+---------+-------------------------------------------------------------------+
| Storage | * Disk availability (Error free disk access time)                 |
|         | * Disk mean-time-to-failure                                       |
|         | * Number of failed storage read/write operations per second       |
|         |                                                                   |
+---------+-------------------------------------------------------------------+

.. _table2_4:

**Table 4 - Yardstick Generic Test Cases**

+---------+-------------------+----------------+------------------------------+
| Category| Performance/Speed | Capacity/Scale | Availability/Reliability     |
|         |                   |                |                              |
+---------+-------------------+----------------+------------------------------+
| Compute | TC003             | TC003          |  TC013 [1]_                  |
|         | TC004             | TC004          |  TC015 [1]_                  |
|         | TC014             | TC010          |                              |
|         | TC024             | TC012          |                              |
|         |                   |                |                              |
+---------+-------------------+----------------+------------------------------+
| Network | TC002             | TC001          |  TC016 [1]_                  |
|         | TC011             | TC008          |  TC018 [1]_                  |
|         |                   | TC009          |                              |
|         |                   |                |                              |
+---------+-------------------+----------------+------------------------------+
| Storage | TC005             | TC005          |  TC017 [1]_                  |
|         |                   |                |                              |
+---------+-------------------+----------------+------------------------------+

.. note:: The description in this OPNFV document is intended as a reference for
  users to understand the scope of the Yardstick Project and the
  deliverables of the Yardstick framework. For complete description of
  the methodology, refer to the ETSI document.

.. rubric:: Footnotes
.. [1] To be included in future deliveries.
