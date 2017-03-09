.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC073
*************************************

.. _netperf: http://www.netperf.org/netperf/training/Netperf.html

+-----------------------------------------------------------------------------+
|Throughput per NFVI node test                                                |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC073_Network latency and throughput between |
|              | nodes                                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Network latency and throughput                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS network performance with regards to     |
|              | flows and throughput, such as if and how different amounts   |
|              | of packet sizes and flows matter for the throughput between  |
|              | nodes in one pod.                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc073.yaml                             |
|              |                                                              |
|              | Packet size: default 1024 bytes.                             |
|              |                                                              |
|              | Test length: default 20 seconds.                             |
|              |                                                              |
|              | The client and server are distributed on different nodes.    |
|              |                                                              |
|              | For SLA max_mean_latency is set to 100.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | netperf_                                                     |
|              | Netperf is a software application that provides network      |
|              | bandwidth testing between two hosts on a network. It         |
|              | supports Unix domain sockets, TCP, SCTP, DLPI and UDP via    |
|              | BSD Sockets. Netperf provides a number of predefined tests   |
|              | e.g. to measure bulk (unidirectional) data transfer or       |
|              | request response performance.                                |
|              | (netperf is not always part of a Linux distribution, hence   |
|              | it needs to be installed.)                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | netperf Man pages                                            |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different packet sizes and       |
|              | test duration. Default values exist.                         |
|              |                                                              |
|              | SLA (optional): max_mean_latency                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The POD can be reached by external ip and logged on via ssh  |
|conditions    |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Install netperf tool on each specified node, one is as the   |
|              | server, and the other as the client.                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Log on to the client node and use the netperf command to     |
|              | execute the network performance test                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | The throughput results stored.                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
