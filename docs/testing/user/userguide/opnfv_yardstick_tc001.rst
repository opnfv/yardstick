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
|test case id  | OPNFV_YARDSTICK_TC001_NETWORK PERFORMANCE                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Number of flows and throughput                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC001 is to evaluate the IaaS network         |
|              | performance with regards to flows and throughput, such as if |
|              | and how different amounts of flows matter for the throughput |
|              | between hosts on different compute blades. Typically e.g.    |
|              | the performance of a vSwitch depends on the number of flows  |
|              | running through it. Also performance of other equipment or   |
|              | entities can depend on the number of flows or the packet     |
|              | sizes used.                                                  |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | pktgen                                                       |
|              |                                                              |
|              | Linux packet generator is a tool to generate packets at very |
|              | high speed in the kernel. pktgen is mainly used to drive and |
|              | LAN equipment test network. pktgen supports multi threading. |
|              | To generate random MAC address, IP address, port number UDP  |
|              | packets, pktgen uses multiple CPU processors in the          |
|              | different PCI bus (PCI, PCIe bus) with Gigabit Ethernet      |
|              | tested (pktgen performance depends on the CPU processing     |
|              | speed, memory delay, PCI bus speed hardware parameters),     |
|              | Transmit data rate can be even larger than 10GBit/s. Visible |
|              | can satisfy most card test requirements.                     |
|              |                                                              |
|              | (Pktgen is not always part of a Linux distribution, hence it |
|              | needs to be installed. It is part of the Yardstick Docker    |
|              | image.                                                       |
|              | As an example see the /yardstick/tools/ directory for how    |
|              | to generate a Linux image with pktgen included.)             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | This test case uses Pktgen to generate packet flow between   |
|description   | two hosts for simulating network workloads on the SUT.       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|traffic       | An IP table is setup on server to monitor for received       |
|profile       | packets.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc001.yaml                             |
|              |                                                              |
|              | Packet size is set to 60 bytes.                              |
|              | Number of ports: 10, 50, 100, 500 and 1000, where each       |
|              | runs for 20 seconds. The whole sequence is run twice         |
|              | The client and server are distributed on different hardware. |
|              |                                                              |
|              | For SLA max_ppm is set to 1000. The amount of configured     |
|              | ports map to between 110 up to 1001000 flows, respectively.  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * packet sizes;                                             |
|              |  * amount of flows;                                          |
|              |  * test duration.                                            |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA (optional): max_ppm: The number of packets per million   |
|              | packets sent that are acceptable to loose, not received.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is used for generating high network           |
|              | throughput to simulate certain workloads on the SUT. Hence   |
|              | it should work with other test cases.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | pktgen_                                                      |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
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
|step 1        | Two host VMs are booted, as server and client.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the server VM by using ssh.      |
|              | 'pktgen_benchmark' bash script is copyied from Jump Host to  |
|              | the server VM via the ssh tunnel.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | An IP table is setup on server to monitor for received       |
|              | packets.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | pktgen is invoked to generate packet flow between two server |
|              | and client for simulating network workloads on the SUT.      |
|              | Results are processed and checked against the SLA. Logs are  |
|              | produced and stored.                                         |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | Two host VMs are deleted.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
