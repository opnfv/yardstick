.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC061
*************************************

.. _man-pages: http://linux.die.net/man/1/sar

+-----------------------------------------------------------------------------+
|Network Utilization                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC061_Network Utilization                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Network utilization                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS network capability with regards to      |
|              | network utilization, including Total number of packets       |
|              | received per second, Total number of packets transmitted per |
|              | second, Total number of kilobytes received per second, Total |
|              | number of kilobytes transmitted per second, Number of        |
|              | compressed packets received per second (for cslip etc.),     |
|              | Number of compressed packets transmitted per second, Number  |
|              | of multicast packets received per second, Utilization        |
|              | percentage of the network interface.                         |
|              | This test case should be run in parallel to other Yardstick  |
|              | test cases and not run as a stand-alone test case.           |
|              | Measure the network usage statistics from the network devices|
|              | Average, minimum and maximun values are obtained.            |
|              | The purpose is also to be able to spot trends.               |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: netutilization.yaml (in the 'samples' directory)       |
|              |                                                              |
|              | * interval: 1 - repeat, pausing every 1 seconds in-between.  |
|              | * count: 1 - display statistics 1 times, then exit.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | sar                                                          |
|              |                                                              |
|              | The sar command writes to standard output the contents of    |
|              | selected cumulative activity counters in the operating       |
|              | system.                                                      |
|              | sar is normally part of a Linux distribution, hence it       |
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
|conditions    | with sar included in the image.                              |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result.                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host is installed as client. The related TC, or TCs, is  |
|              | invoked and sar logs are produced and stored.                |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Network utilization results are fetched and stored.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
