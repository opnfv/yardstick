.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC076
*************************************


+-----------------------------------------------------------------------------+
|Monitor Network Metrics                                                      |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC076_Monitor_Network_Metrics                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | IP datagram error rate, ICMP message error rate,             |
|              | TCP segment error rate and UDP datagram error rate           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | Monitor network metrics provided by the kernel in a host and |
|              | calculate IP datagram error rate, ICMP message error rate,   |
|              | TCP segment error rate and UDP datagram error rate.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc076.yaml                             |
|              |                                                              |
|              | There is no additional configuration to be set for this TC.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | nstat                                                        |
|              |                                                              |
|              | nstat is a simple tool to monitor kernel snmp counters and   |
|              | network interface statistics.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | nstat man page                                               |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This test case is mainly for monitoring network metrics.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre_test      |                                                              |
|conditions    |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The pod is available.                                        |
|              | Nstat is invoked and logs are produced and stored.           |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None.                                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
