.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC004
*************************************

.. _cachestat: https://github.com/brendangregg/perf-tools/tree/master/fs

+-----------------------------------------------------------------------------+
|Cache Utilization                                                            |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC004_CACHE Utilization                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | cache hit, cache miss, hit/miss ratio, buffer size and page  |
|              | cache size                                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC004 is to evaluate the IaaS compute         |
|              | capability with regards to cache utilization.This test case  |
|              | should be run in parallel with other Yardstick test cases    |
|              | and not run as a stand-alone test case.                      |
|              |                                                              |
|              | This test case measures cache usage statistics, including    |
|              | cache hit, cache miss, hit ratio, buffer cache size and page |
|              | cache size, with some wokloads runing on the infrastructure. |
|              | Both average and maximun values are collected.               |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | cachestat                                                    |
|              |                                                              |
|              | cachestat is a tool using Linux ftrace capabilities for      |
|              | showing Linux page cache hit/miss statistics.                |
|              |                                                              |
|              | (cachestat is not always part of a Linux distribution, hence |
|              | it needs to be installed. As an example see the              |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with cachestat included.)                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | cachestat test is invoked in a host VM on a compute blade,   |
|description   | cachestat test requires some other test cases running in the |
|              | host to stimulate workload.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: cachestat.yaml (in the 'samples' directory)            |
|              |                                                              |
|              | Interval is set 1. Test repeat, pausing every 1 seconds      |
|              | in-between.                                                  |
|              | Test durarion is set to 60 seconds.                          |
|              |                                                              |
|              | SLA is not available in this test case.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * interval;                                                 |
|              |  * runner Duration.                                          |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | cachestat_                                                   |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with cachestat included in the image.                        |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A host VM with cachestat installed is booted.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | 'cache_stat' bash script is copyied from Jump Host to        |
|              | the server VM via the ssh tunnel.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | 'cache_stat' script is invoked. Raw cache usage statistics   |
|              | are collected and filtrated. Average and maximum values are  |
|              | calculated and recorded. Logs are produced and stored.       |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The host VM is deleted.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Cache utilization results are collected and stored.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
