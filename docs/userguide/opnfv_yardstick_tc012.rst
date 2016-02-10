.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC012
*************************************

.. _man-pages: http://manpages.ubuntu.com/manpages/trusty/bw_mem.8.html

+-----------------------------------------------------------------------------+
|Memory Bandwidth                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC012_Memory Bandwidth                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Megabyte per second (MBps)                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | Measure the rate at which data can be read from and written  |
|              | to the memory (this includes all levels of memory).          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: opnfv_yardstick_tc012.yaml                             |
|              |                                                              |
|              | * SLA (optional): 15000 (MBps) min_bw: The minimum amount of |
|              |   memory bandwidth that is accepted.                         |
|              | * Size: 10 240 kB - test allocates twice that size (20 480kB)|
|              |   zeros it and then measures the time it takes to copy from  |
|              |   one side to another.                                       |
|              | * Benchmark: rdwr - measures the time to read data into      |
|              |   memory and then write data to the same location.           |
|              | * Warmup: 0 - the number of iterations to perform before     |
|              |   taking actual measurements.                                |
|              | * Iterations: 10 - test is run 10 times iteratively.         |
|              | * Interval: 1 - there is 1 second delay between each         |
|              |   iteration.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Lmbench                                                      |
|              |                                                              |
|              | Lmbench is a suite of operating system microbenchmarks. This |
|              | test uses bw_mem tool from that suite.                       |
|              | Lmbench is not always part of a Linux distribution, hence it |
|              | needs to be installed in the test image.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | man-pages_                                                   |
|              |                                                              |
|              | McVoy, Larry W., and Carl Staelin. "lmbench: Portable Tools  |
|              | for Performance Analysis." USENIX annual technical           |
|              | conference. 1996.                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * memory sizes;                                             |
|              |  * memory operations (such as rd, wr, rdwr, cp, frd, fwr,    |
|              |    fcp, bzero, bcopy);                                       |
|              |  * number of warmup iterations;                              |
|              |  * iterations and intervals.                                 |
|              |                                                              |
|              | There are default values for each above-mentioned option.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with Lmbench included in the image.                          |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host is installed as client. Lmbench's bw_mem tool is    |
|              | invoked and  logs are produced and stored.                   |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test fails if the measured memory bandwidth is below the SLA |
|              | value or if there is a test case execution problem.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
