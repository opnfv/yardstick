.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC010
*************************************

.. _lat_mem_rd: http://manpages.ubuntu.com/manpages/trusty/lat_mem_rd.8.html

+-----------------------------------------------------------------------------+
|Memory Latency                                                               |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC010_MEMORY LATENCY                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Memory read latency (nanoseconds)                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC010 is to evaluate the IaaS compute         |
|              | performance with regards to memory read latency.             |
|              | It measures the memory read latency for varying memory sizes |
|              | and strides. Whole memory hierarchy is measured.             |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Lmbench                                                      |
|              |                                                              |
|              | Lmbench is a suite of operating system microbenchmarks. This |
|              | test uses lat_mem_rd tool from that suite including:         |
|              |  * Context switching                                         |
|              |  * Networking: connection establishment, pipe, TCP, UDP, and |
|              |    RPC hot potato                                            |
|              |  * File system creates and deletes                           |
|              |  * Process creation                                          |
|              |  * Signal handling                                           |
|              |  * System call overhead                                      |
|              |  * Memory read latency                                       |
|              |                                                              |
|              | (LMbench is not always part of a Linux distribution, hence   |
|              | it needs to be installed. As an example see the              |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with LMbench included.)                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | LMbench lat_mem_rd benchmark measures memory read latency    |
|description   | for varying memory sizes and strides.                        |
|              |                                                              |
|              | The benchmark runs as two nested loops. The outer loop is    |
|              | the stride size. The inner loop is the array size. For each  |
|              | array size, the benchmark creates a ring of pointers that    |
|              | point backward one stride.Traversing the array is done by:   |
|              |                                                              |
|              |         p = (char **)*p;                                     |
|              |                                                              |
|              | in a for loop (the over head of the for loop is not          |
|              | significant; the loop is an unrolled loop 100 loads long).   |
|              | The size of the array varies from 512 bytes to (typically)   |
|              | eight megabytes. For the small sizes, the cache will have an |
|              | effect, and the loads will be much faster. This becomes much |
|              | more apparent when the data is plotted.                      |
|              |                                                              |
|              | Only data accesses are measured; the instruction cache is    |
|              | not measured.                                                |
|              |                                                              |
|              | The results are reported in nanoseconds per load and have    |
|              | been verified accurate to within a few nanoseconds on an SGI |
|              | Indy.                                                        |
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
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably lower read latency is expected.        |
|              | However, to cover most configurations, both baremetal and    |
|              | fully virtualized  ones, this value should be possible to    |
|              | achieve and acceptable for black box testing.                |
|              | Many heavy IO applications start to suffer badly if the      |
|              | read latency is higher than this.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              | * strides;                                                   |
|              | * stop_size;                                                 |
|              | * iterations and intervals.                                  |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA (optional) : max_latency: The maximum memory latency     |
|              | that is accepted.                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | LMbench lat_mem_rd_                                          |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
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
|step 1        | The host is installed as client. LMbench's lat_mem_rd tool   |
|              | is invoked and logs are produced and stored.                 |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A host VM with LMbench installed is booted.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | 'lmbench_latency_benchmark' bash script is copyied from Jump |
|              | Host to the host VM via the ssh tunnel.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | 'lmbench_latency_benchmark' script is invoked. LMbench's     |
|              | lat_mem_rd benchmark starts to measures memory read latency  |
|              | for varying memory sizes and strides. Memory read latency    |
|              | are recorded and checked against the SLA. Logs are produced  |
|              | and stored.                                                  |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The host VM is deleted.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test fails if the measured memory latency is above the SLA   |
|              | value or if there is a test case execution problem.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
