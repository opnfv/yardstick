.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC001
*************************************

.. _pktgen: https://www.kernel.org/doc/Documentation/networking/pktgen.txt

+-----------------------------------------------------------------------------+
|Network Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC001_NW PERF                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Number of flows and throughput                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS network performance with regards to     |
|              | flows and throughput, such as if and how different amounts   |
|              | of flows matter for the throughput between hosts on different|
|              | compute blades. Typically e.g. the performance of a vSwitch  |
|              | depends on the number of flows running through it. Also      |
|              | performance of other equipment or entities can depend        |
|              | on the number of flows or the packet sizes used.             |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs ans similar shall be stored for comparison reasons and|
|              | product evolution understanding between different OPNFV      |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc001.yaml                             |
|              |                                                              |
|              | Packet size: 60 bytes                                        |
|              | Number of ports: 10, 50, 100, 500 and 1000, where each       |
|              | runs for 20 seconds. The whole sequence is run               |
|              | twice. The client and server are distributed on different HW.|
|              | For SLA max_ppm is set to 1000. The amount of configured     |
|              | ports map to between 110 up to 1001000 flows, respectively.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | pktgen                                                       |
|              |                                                              |
|              | (Pktgen is not always part of a Linux distribution, hence it |
|              | needs to be installed. It is part of the Yardstick Docker    |
|              | image.                                                       |
|              | As an example see the /yardstick/tools/ directory for how    |
|              | to generate a Linux image with pktgen included.)             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | pktgen_                                                      |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different packet sizes, amount   |
|              | of flows and test duration. Default values exist.            |
|              |                                                              |
|              | SLA (optional): max_ppm: The number of packets per million   |
|              |  packets sent that are acceptable to loose, not received.    |
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
