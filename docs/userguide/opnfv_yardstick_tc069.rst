.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC069
*************************************

.. _RAMspeed: http://alasir.com/software/ramspeed/

.. table::
    :class: longtable

+-----------------------------------------------------------------------------+
|Memory Bandwidth                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC069_Memory Bandwidth                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Megabyte per second (MBps)                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS compute performance with regards to     |
|              | memory bandwidth.                                            |
|              | Measure the maximum possible cache and memory performance    |
|              | while reading and writing certain blocks of data (starting   |
|              | from 1Kb and further in power of 2) continuously through ALU |
|              | and FPU respectively.                                        |
|              | Measure different aspects of memory performance via          |
|              | synthetic simulations. Each simulation consists of four      |
|              | performances (Copy, Scale, Add, Triad).                      |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: opnfv_yardstick_tc069.yaml                             |
|              |                                                              |
|              | * SLA (optional): 7000 (MBps) min_bandwidth: The minimum     |
|              |   amount of memory bandwidth that is accepted.               |
|              | * type_id: 1 - runs a specified benchmark                    |
|              |   (by an ID number):                                         |
|              |     1 -- INTmark [writing]          4 -- FLOATmark [writing] |
|              |     2 -- INTmark [reading]          5 -- FLOATmark [reading] |
|              |     3 -- INTmem                     6 -- FLOATmem            |
|              | * block_size: 64 Megabytes - the maximum block               |
|              |               size per array.                                |
|              | * load: 32 Gigabytes - the amount of data load per pass.     |
|              | * iterations: 5 - test is run 5   times iteratively.         |
|              | * interval: 1 - there is 1 second delay between each         |
|              |   iteration.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | RAMspeed                                                     |
|              |                                                              |
|              | RAMspeed is a free open source command line utility to       |
|              | measure cache and memory performance of computer systems.    |
|              | RAMspeed is not always part of a Linux distribution, hence   |
|              | it needs to be installed in the test image.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | RAMspeed_                                                    |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * benchmark operations (such as INTmark [writing],          |
|              |    INTmark [reading], FLOATmark [writing],                   |
|              |    FLOATmark [reading], INTmem, FLOATmem);                   |
|              |  * block size per array;                                     |
|              |  * load per pass;                                            |
|              |  * number of batch run iterations;                           |
|              |  * iterations and intervals.                                 |
|              |                                                              |
|              | There are default values for each above-mentioned option.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with RAmspeed included in the image.                         |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host is installed as client. RAMspeed is invoked and     |
|              | logs are produced and stored.                                |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test fails if the measured memory bandwidth is below the SLA |
|              | value or if there is a test case execution problem.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
