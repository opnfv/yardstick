.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC071
*************************************

.. _cirros: https://download.cirros-cloud.net
.. _pktgen: https://www.kernel.org/doc/Documentation/networking/pktgen.txt
.. _cachestat: https://github.com/brendangregg/perf-tools/tree/master/fs

+-----------------------------------------------------------------------------+
|Latency, Cache Utilization, Throughput, Packet Loss                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC071_Latency, Cache Utilization,            |
|              | Throughput,Packet Loss                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Number of flows, latency, throughput, Cache Utilization,     |
|              | packet loss                                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS network performance with regards to     |
|              | flows and throughput, such as if and how different amounts   |
|              | of flows matter for the throughput between hosts on different|
|              | compute blades. Typically e.g. the performance of a vSwitch  |
|              | depends on the number of flows running through it. Also      |
|              | performance of other equipment or entities can depend        |
|              | on the number of flows or the packet sizes used.             |
|              | The purpose is also to be able to spot trends.               |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc071.yaml                             |
|              |                                                              |
|              | Packet size: 64 bytes                                        |
|              | Number of ports: 1, 10, 50, 100, 300, 500, 750 and 1000.     |
|              | The amount configured ports map from 2 up to 1001000 flows,  |
|              | respectively. Each port amount is run two times, for 20      |
|              | seconds each. Then the next port_amount is run, and so on.   |
|              | During the test Cache Utilization on both client and server, |
|              | and the network latency between the client and server are    |
|              | measured.                                                    |
|              | The client and server are distributed on different HW.       |
|              | For SLA max_ppm is set to 1000.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | pktgen                                                       |
|              |                                                              |
|              | Pktgen is not always part of a Linux distribution, hence it  |
|              | needs to be installed. It is part of the Yardstick Glance    |
|              | image.                                                       |
|              | (As an example see the /yardstick/tools/ directory for how   |
|              | to generate a Linux image with pktgen included.)             |
|              |                                                              |
|              | ping                                                         |
|              |                                                              |
|              | Ping is normally part of any Linux distribution, hence it    |
|              | doesn't need to be installed. It is also part of the         |
|              | Yardstick Glance image.                                      |
|              | (For example also a cirros_ image can be downloaded, it      |
|              | includes ping)                                               |
|              |                                                              |
|              | cachestat                                                    |
|              |                                                              |
|              | cachestat is not always part of a Linux distribution, hence  |
|              | it needs to be installed.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Ping man pages                                               |
|              |                                                              |
|              | pktgen_                                                      |
|              |                                                              |
|              | cachestat_                                                   |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different packet sizes, amount   |
|              | of flows and test duration. Default values exist.            |
|              |                                                              |
|              | SLA (optional): max_ppm: The number of packets per million   |
|              | packets sent that are acceptable to lose, not received.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with pktgen included in it.                                  |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed, as server and client. pktgen is     |
|              | invoked and logs are produced and stored.                    |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
