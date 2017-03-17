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
|test purpose  | The purpose of TC076 is to evaluate the IaaS network         |
|              | reliability with regards to IP datagram error rate, ICMP     |
|              | message error rate, TCP segment error rate and UDP datagram  |
|              | error rate.                                                  |
|              |                                                              |
|              | TC076 monitors network metrics provided by the Linux kernel  |
|              | in a host and calculates IP datagram error rate, ICMP        |
|              | message error rate, TCP segment error rate and UDP datagram  |
|              | error rate.                                                  |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | nstat                                                        |
|              |                                                              |
|              | nstat is a simple tool to monitor kernel snmp counters and   |
|              | network interface statistics.                                |
|              |                                                              |
|              | (nstat is not always part of a Linux distribution, hence it  |
|              | needs to be installed. nstat is provided by the iproute2     |
|              | collection, which is usually also the name of the package in |
|              | many Linux distributions.As an example see the               |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with iproute2 included.)                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | Ping packets (ICMP protocol's mandatory ECHO_REQUEST         |
|description   | datagram) are sent from host VM to target VM(s) to elicit    |
|              | ICMP ECHO_RESPONSE.                                          |
|              |                                                              |
|              | nstat is invoked on the target vm to monitors network        |
|              | metrics provided by the Linux kernel.                        |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc076.yaml                             |
|              |                                                              |
|              | There is no additional configuration to be set for this TC.  |
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
|pre_test      | The test case image needs to be installed into Glance        |
|conditions    | with fio included in it.                                     |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Two host VMs are booted, as server and client.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the server VM by using ssh.      |
|              | 'ping_benchmark' bash script is copyied from Jump Host to    |
|              | the server VM via the ssh tunnel.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Ping is invoked. Ping packets are sent from server VM to     |
|              | client VM. RTT results are calculated and checked against    |
|              | the SLA. nstat is invoked on the client vm to monitors       |
|              | network metrics provided by the Linux kernel. IP datagram    |
|              | error rate, ICMP message error rate, TCP segment error rate  |
|              | and UDP datagram error rate are calculated.                  |
|              | Logs are produced and stored.                                |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Two host VMs are deleted.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None.                                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
