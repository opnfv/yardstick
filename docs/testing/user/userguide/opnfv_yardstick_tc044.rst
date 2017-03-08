.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC044
*************************************

.. _man-pages: http://manpages.ubuntu.com/manpages/trusty/en/man1/free.1.html

+-----------------------------------------------------------------------------+
|Memory Utilization                                                           |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC044_Memory Utilization                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Memory utilization                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS compute capability with regards to      |
|              | memory utilization.This test case should be run in parallel  |
|              | to other Yardstick test cases and not run as a stand-alone   |
|              | test case.                                                   |
|              | Measure the memory usage statistics including used memory,   |
|              | free memory, buffer, cache and shared memory.                |
|              | Both average and maximun values are obtained.                |
|              | The purpose is also to be able to spot trends.               |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: memload.yaml (in the 'samples' directory)              |
|              |                                                              |
|              | * interval: 1 - repeat, pausing every 1 seconds in-between.  |
|              | * count: 10 - display statistics 10 times, then exit.        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | free                                                         |
|              |                                                              |
|              | free provides information about unused and used memory and   |
|              | swap space on any computer running Linux or another Unix-like|
|              | operating system.                                            |
|              | free is normally part of a Linux distribution, hence it      |
|              | doesn't needs to be installed.                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | man-pages_                                                   |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * interval;                                                 |
|              |  * count;                                                    |
|              |  * runner Iteration and intervals.                           |
|              |                                                              |
|              | There are default values for each above-mentioned option.    |
|              | Run in background with other test cases.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with free included in the image.                             |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host is installed as client. The related TC, or TCs, is  |
|              | invoked and free logs are produced and stored.               |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Memory utilization results are fetched and stored.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
