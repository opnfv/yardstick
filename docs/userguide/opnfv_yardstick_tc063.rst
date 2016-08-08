.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC063
*************************************

+-----------------------------------------------------------------------------+
|Storage Capacity                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC063_Storage Capacity                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Storage/disk size                                            |                                                                  
|              | Disk Utilization                                             |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will check the parameters which could decide  |
|              | several models and each model has its specified task to      |
|              | measure. The test purposes are to measure disk size, block   |
|              | size and disk utilization. With the test results, we could   |
|              | evaluate the storage capacity of disk.                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: file: opnfv_yardstick_tc063.yaml                       |
|              |                                                              |
|              |* test_type: "disk_size"                                      |
|              |* runner:                                                     |
|              |    type: Iteration                                           |
|              |    iterations: 1- test is run 1 time iteratively.            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | fdisk                                                        |
|              | A command-line utility that provides disk partitioning       |
|              | functions                                                    |
|              |                                                              |
|              | iostat                                                       |
|              | This is a computer system monitor tool used to collect and   |
|              | show operating system storage input and output statistics.   |
+--------------+--------------------------------------------------------------+
|references    | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * test_type;                                                |
|              |  * interval: 1 - how ofter to stat disk utilization          |
|              |       type: int                                              |
|              |       unit: seconds                                          |
|              |  * count: 15 - how many times to stat disk utilization       |
|              |     type: int                                                |
|              |     unit: na                                                 |
|              | There are default values for each above-mentioned option.    |
|              | Run in background with other test cases.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | Output the specific storage capacity of disk information as  |
|              | the sequence into file.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed.                                     |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None.                                                        |
+--------------+--------------------------------------------------------------+
