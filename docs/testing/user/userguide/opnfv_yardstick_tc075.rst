.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC075
*************************************


+-----------------------------------------------------------------------------+
|Network Capacity and Scale Testing                                           |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC075_Network_Capacity_and_Scale_testing     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Number of connections, Number of frames sent/received        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the network capacity and scale with regards to   |
|              | connections and frmaes.                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc075.yaml                             |
|              |                                                              |
|              | There is no additional configuration to be set for this TC.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | netstar                                                      |
|              |                                                              |
|              | Netstat is normally part of any Linux distribution, hence it |
|              | doesn't need to be installed.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Netstat man page                                             |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This test case is mainly for evaluating network performance. |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre_test      | Each pod node must have netstat included in it.              |
|conditions    |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The pod is available.                                        |
|              | Netstat is invoked and logs are produced and stored.         |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. Number of connections and frames are fetched and       |
|              | stored.                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
