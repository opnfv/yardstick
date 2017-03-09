.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC037
*************************************

.. _cirros-image: https://download.cirros-cloud.net
.. _Ping: https://linux.die.net/man/8/ping
.. _pktgen: https://www.kernel.org/doc/Documentation/networking/pktgen.txt
.. _mpstat: http://www.linuxcommand.org/man_pages/mpstat1.html

+-----------------------------------------------------------------------------+
|Latency, CPU Load, Throughput, Packet Loss                                   |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC037_LATENCY,CPU LOAD,THROUGHPUT,           |
|              | PACKET LOSS                                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | Number of flows, latency, throughput, packet loss            |
|              | CPU utilization percentage, CPU interrupt per second         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC037 is to evaluate the IaaS compute         |
|              | capacity and network performance with regards to CPU         |
|              | utilization, packet flows and network throughput, such as if |
|              | and how different amounts of flows matter for the throughput |
|              | between hosts on different compute blades, and the CPU load  |
|              | variation.                                                   |
|              |                                                              |
|              | Typically e.g. the performance of a vSwitch depends on the   |
|              | number of flows running through it. Also performance of      |
|              | other equipment or entities can depend on the number of      |
|              | flows or the packet sizes used                               |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Ping, Pktgen, mpstat                                         |
|              |                                                              |
|              | Ping is a computer network administration software utility   |
|              | used to test the reachability of a host on an Internet       |
|              | Protocol (IP) network. It measures the round-trip time for   |
|              | packet sent from the originating host to a destination       |
|              | computer that are echoed back to the source.                 |
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
|              | The mpstat command writes to standard output activities for  |
|              | each available processor, processor 0 being the first one.   |
|              | Global average activities among all processors are also      |
|              | reported. The mpstat command can be used both on SMP and UP  |
|              | machines, but in the latter, only global average activities  |
|              | will be printed.                                             |
|              |                                                              |
|              | (Ping is normally part of any Linux distribution, hence it   |
|              | doesn't need to be installed. It is also part of the         |
|              | Yardstick Docker image.                                      |
|              | For example also a Cirros image can be downloaded from       |
|              | cirros-image_, it includes ping.                             |
|              |                                                              |
|              | Pktgen and mpstat are not always part of a Linux             |
|              | distribution, hence it needs to be installed. It is part of  |
|              | the Yardstick Docker image.                                  |
|              | As an example see the /yardstick/tools/ directory for how    |
|              | to generate a Linux image with pktgen and mpstat included.)  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | This test case uses Pktgen to generate packet flow between   |
|description   | two hosts for simulating network workloads on the SUT.       |
|              | Ping packets (ICMP protocol's mandatory ECHO_REQUEST         |
|              | datagram) are sent from a host VM to the target VM(s) to     |
|              | elicit ICMP ECHO_RESPONSE, meanwhile CPU activities are      |
|              | monitored by mpstat.                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc037.yaml                             |
|              |                                                              |
|              | Packet size is set to 64 bytes.                              |
|              | Number of ports: 1, 10, 50, 100, 300, 500, 750 and 1000.     |
|              | The amount configured ports map from 2 up to 1001000 flows,  |
|              | respectively. Each port amount is run two times, for 20      |
|              | seconds each. Then the next port_amount is run, and so on.   |
|              | During the test CPU load on both client and server, and the  |
|              | network latency between the client and server are measured.  |
|              | The client and server are distributed on different hardware. |
|              | mpstat monitoring interval is set to 1 second.               |
|              | ping packet size is set to 100 bytes.                        |
|              | For SLA max_ppm is set to 1000.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * pktgen packet sizes;                                      |
|              |  * amount of flows;                                          |
|              |  * test duration;                                            |
|              |  * ping packet size;                                         |
|              |  * mpstat monitor interval.                                  |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA (optional): max_ppm: The number of packets per million   |
|              | packets sent that are acceptable to loose, not received.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Ping_                                                        |
|              |                                                              |
|              | mpstat_                                                      |
|              |                                                              |
|              | pktgen_                                                      |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with pktgen, mpstat included in it.                          |
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
|              | 'pktgen_benchmark', "ping_benchmark" bash script are copyied |
|              | from Jump Host to the server VM via the ssh tunnel.          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | An IP table is setup on server to monitor for received       |
|              | packets.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | pktgen is invoked to generate packet flow between two server |
|              | and client for simulating network workloads on the SUT. Ping |
|              | is invoked. Ping packets are sent from server VM to client   |
|              | VM. mpstat is invoked, recording activities for each         |
|              | available processor. Results are processed and checked       |
|              | against the SLA. Logs are produced and stored.               |
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
