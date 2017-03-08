.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, ZTE and others.

***************************************
Yardstick Test Case Description TC0042
***************************************

.. _DPDK: http://dpdk.org/doc/guides/index.html
.. _Testpmd: http://dpdk.org/doc/guides/testpmd_app_ug/index.html
.. _Pktgen-dpdk: http://pktgen.readthedocs.io/en/latest/index.html

+-----------------------------------------------------------------------------+
|Network Performance                                                          |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC042_DPDK pktgen latency measurements       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | L2 Network Latency                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | Measure L2 network latency when DPDK is enabled between hosts|
|              | on different compute blades.                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc042.yaml                             |
|              |                                                              |
|              | * Packet size: 64 bytes                                      |
|              | * SLA(max_latency): 100usec                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | DPDK_                                                        |
|              | Pktgen-dpdk_                                                 |
|              |                                                              |
|              | (DPDK and Pktgen-dpdk are not part of a Linux distribution,  |
|              | hence they needs to be installed.                            |
|              | As an example see the /yardstick/tools/ directory for how to |
|              | generate a Linux image with DPDK and pktgen-dpdk included.)  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | DPDK_                                                        |
|              |                                                              |
|              | Pktgen-dpdk_                                                 |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different packet sizes. Default  |
|              | values exist.                                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with DPDK and pktgen-dpdk included in it.                    |
|              |                                                              |
|              | The NICs of compute nodes must support DPDK on POD.          |
|              |                                                              |
|              | And at least compute nodes setup hugepage.                   |
|              |                                                              |
|              | If you want to achievement a hight performance result, it is |
|              | recommend to use NUAM, CPU pin, OVS and so on.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed on different blades, as server and   |
|              | client. Both server and client have three interfaces. The    |
|              | first one is management such as ssh. The other two are used  |
|              | by DPDK.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Testpmd_ is invoked with configurations to forward packets   |
|              | from one DPDK port to the other on server.                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Pktgen-dpdk is invoked with configurations as a traffic      |
|              | generator and logs are produced and stored on client.        |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
