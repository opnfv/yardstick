.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC010
*************************************

.. _man-pages: http://manpages.ubuntu.com/manpages/trusty/lat_mem_rd.8.html

+-----------------------------------------------------------------------------+
|Memory Latency                                                               |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC010_Memory Latency                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Latency in nanoseconds                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | Measure the memory read latency for varying memory sizes and |
|              | strides. Whole memory hierarchy is measured including all    |
|              | levels of cache.                                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: opnfv_yardstick_tc010.yaml                             |
|              |                                                              |
|              | * SLA (max_latency): 30 nanoseconds                          |
|              | * Stride - 128 bytes                                         |
|              | * Stop size - 64 megabytes                                   |
|              | * Iterations: 10 - test is run 10 times iteratively.         |
|              | * Interval: 1 - there is 1 second delay between each         |
|              |   iteration.                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Lmbench                                                      |
|              |                                                              |
|              | Lmbench is a suite of operating system microbenchmarks. This |
|              | test uses lat_mem_rd tool from that suite.                   |
|              | Lmbench is not always part of a Linux distribution, hence it |
|              | needs to be installed in the test image                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | man-pages_                                                   |
|              |                                                              |
|              | McVoy, Larry W.,and Carl Staelin. "lmbench: Portable Tools   |
|              | for Performance Analysis." USENIX annual technical           |
|              | conference 1996.                                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              | * strides;                                                   |
|              | * stop_size;                                                 |
|              | * iterations and intervals.                                  |
|              |                                                              |
|              | There are default values for each above-mentioned option.    |
|              |                                                              |
|              | SLA (optional) : max_latency: The maximum memory latency     |
|              | that is accepted.                                            |
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
|step 1        | The host is installed as client. Lmbench's lat_mem_rd tool   |
|              | is invoked and logs are produced and stored.                 |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test fails if the measured memory latency is above the SLA   |
|              | value or if there is a test case execution problem.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
