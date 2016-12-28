.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC012
*************************************

.. _bw_mem: http://manpages.ubuntu.com/manpages/trusty/bw_mem.8.html

+-----------------------------------------------------------------------------+
|Memory Bandwidth                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC012_MEMORY BANDWIDTH                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Memory read/write bandwidth (MBps)                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC012 is to evaluate the IaaS compute         |
|              | performance with regards to memory throughput.               |
|              | It measures the rate at which data can be read from and      |
|              | written to the memory (this includes all levels of memory).  |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | LMbench                                                      |
|              |                                                              |
|              | LMbench is a suite of operating system microbenchmarks.      |
|              | This test uses bw_mem tool from that suite including:        |
|              |  * Cached file read                                          |
|              |  * Memory copy (bcopy)                                       |
|              |  * Memory read                                               |
|              |  * Memory write                                              |
|              |  * Pipe                                                      |
|              |  * TCP                                                       |
|              |                                                              |
|              | (LMbench is not always part of a Linux distribution, hence   |
|              | it needs to be installed. As an example see the              |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with LMbench included.)                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | LMbench bw_mem benchmark allocates twice the specified       |
|description   | amount of memory, zeros it, and then times the copying of    |
|              | the first half to the second half. The benchmark is invoked  |
|              | in a host VM on a compute blade. Results are reported in     |
|              | megabytes moved per second.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: opnfv_yardstick_tc012.yaml                             |
|              |                                                              |
|              | * SLA (optional): 15000 (MBps) min_bw: The minimum amount of |
|              |   memory bandwidth that is accepted.                         |
|              | * Size: 10 240 kB - test allocates twice that size           |
|              |   (20 480kB) zeros it and then measures the time it takes to |
|              |   copy from one side to another.                             |
|              | * Benchmark: rdwr - measures the time to read data into      |
|              |   memory and then write data to the same location.           |
|              | * Warmup: 0 - the number of iterations to perform before     |
|              |   taking actual measurements.                                |
|              | * Iterations: 10 - test is run 10 times iteratively.         |
|              | * Interval: 1 - there is 1 second delay between each         |
|              |   iteration.                                                 |
|              |                                                              |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably higher bandwidth is expected.          |
|              | However, to cover most configurations, both baremetal and    |
|              | fully virtualized  ones, this value should be possible to    |
|              | achieve and acceptable for black box testing.                |
|              | Many heavy IO applications start to suffer badly if the      |
|              | read/write bandwidths are lower than this.                   |
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
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA (optional) : min_bandwidth: The minimun memory bandwidth |
|              | that is accepted.                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | LMbench bw_mem_                                              |
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
|step 1        | A host VM with LMbench installed is booted.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | "lmbench_bandwidth_benchmark" bash script is copied from     |
|              | Jump Host to the host VM via ssh tunnel.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | 'lmbench_bandwidth_benchmark' script is invoked. LMbench's   |
|              | bw_mem benchmark starts to measures memory read/write        |
|              | bandwidth. Memory read/write bandwidth results are recorded  |
|              | and checked against the SLA. Logs are produced and stored.   |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The host VM is deleted.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test fails if the measured memory bandwidth is below the SLA |
|              | value or if there is a test case execution problem.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
