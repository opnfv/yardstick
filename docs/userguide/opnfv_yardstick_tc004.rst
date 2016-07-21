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
|test case id  | OPNFV_YARDSTICK_TC004_Cache Utilization                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Cache Utilization                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS compute capability with regards to      |
|              | cache utilization.This test case should be run in parallel   |
|              | to other Yardstick test cases and not run as a stand-alone   |
|              | test case.                                                   |
|              | Measure the cache usage statistics including cache hit,      |
|              | cache miss, hit ratio, page cache size and page cache size.  |
|              | Both average and maximun values are obtained.                |
|              | The purpose is also to be able to spot trends.               |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: cachestat.yaml (in the 'samples' directory)            |
|              |                                                              |
|              | * interval: 1 - repeat, pausing every 1 seconds in-between.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | cachestat                                                    |
|              |                                                              |
|              | cachestat is not always part of a Linux distribution, hence  |
|              | it needs to be installed.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | cachestat_                                                   |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * interval;                                                 |
|              |  * runner Duration.                                          |
|              |                                                              |
|              | There are default values for each above-mentioned option.    |
|              | Run in background with other test cases.                     |
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
|step 1        | The host is installed as client. The related TC, or TCs, is  |
|              | invoked and cachestat logs are produced and stored.          |
|              |                                                              |
|              | Result: logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Cache utilization results are fetched and stored.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
