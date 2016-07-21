.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC055
*************************************

.. _/proc/cpuinfo: http://www.linfo.org/proc_cpuinfo.html

+-----------------------------------------------------------------------------+
|Compute Capacity                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC055_Compute Capacity                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Number of cpus, number of cores, number of threads, available|
|              | memory size and total cache size.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS compute capacity with regards to        |
|              | hardware specification, including number of cpus, number of  |
|              | cores, number of threads, available memory size and total    |
|              | cache size.                                                  |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc055.yaml                             |
|              |                                                              |
|              | There is are no additional configurations to be set for this |
|              | TC.                                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | /proc/cpuinfo                                                |
|              |                                                              |
|              | this TC uses /proc/cpuinfo as source to produce compute      |
|              | capacity output.                                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | /proc/cpuinfo_                                               |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | None.                                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | No POD specific requirements have been identified.           |
|conditions    |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed, TC is invoked and logs are produced |
|              | and stored.                                                  |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Hardware specification are fetched and stored.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
