.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC005
*************************************

.. _fio: http://www.bluestop.org/fio/HOWTO.txt

+-----------------------------------------------------------------------------+
|Storage Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC005_Storage Performance                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | IOPS, throughput and latency                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS storage performance with regards to     |
|              | IOPS, throughput and latency.                                |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs and similar shall be stored for comparison reasons    |
|              | and product evolution understanding between different OPNFV  |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc005.yaml                             |
|              |                                                              |
|              | IO types: read, write, randwrite, randread, rw               |
|              | IO block size: 4KB, 64KB, 1024KB, where each                 |
|              | runs for 30 seconds(10 for ramp time, 20 for runtime).       |
|              |                                                              |
|              | For SLA minimum read/write iops is set to 100, minimum       |
|              | read/write throughput is set to 400 KB/s, and maximum        |
|              | read/write latency is set to 20000 usec.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | fio                                                          |
|              |                                                              |
|              | (fio is not always part of a Linux distribution, hence it    |
|              | needs to be installed. As an example see the                 |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with fio included.)                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | fio_                                                         |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different read/write types, IO   |
|              | block size, IO depth, ramp time (runtime required for stable |
|              | results) and test duration. Default values exist.            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with fio included in it.                                     |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host is installed and fio is invoked and logs are        |
|              | produced and stored.                                         |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
