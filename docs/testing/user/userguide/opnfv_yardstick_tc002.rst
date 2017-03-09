.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC002
*************************************

.. _cirros-image: https://download.cirros-cloud.net
.. _Ping: https://linux.die.net/man/8/ping

+-----------------------------------------------------------------------------+
|Network Latency                                                              |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC002_NETWORK LATENCY                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | RTT (Round Trip Time)                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC002 is to do a basic verification that      |
|              | network latency is within acceptable boundaries when packets |
|              | travel between hosts located on same or different compute    |
|              | blades.                                                      |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | ping                                                         |
|              |                                                              |
|              | Ping is a computer network administration software utility   |
|              | used to test the reachability of a host on an Internet       |
|              | Protocol (IP) network. It measures the round-trip time for   |
|              | packet sent from the originating host to a destination       |
|              | computer that are echoed back to the source.                 |
|              |                                                              |
|              | Ping is normally part of any Linux distribution, hence it    |
|              | doesn't need to be installed. It is also part of the         |
|              | Yardstick Docker image.                                      |
|              | (For example also a Cirros image can be downloaded from      |
|              | cirros-image_, it includes ping)                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test topology | Ping packets (ICMP protocol's mandatory ECHO_REQUEST         |
|              | datagram) are sent from host VM to target VM(s) to elicit    |
|              | ICMP ECHO_RESPONSE.                                          |
|              |                                                              |
|              | For one host VM there can be multiple target VMs.            |
|              | Host VM and target VM(s) can be on same or different compute |
|              | blades.                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc002.yaml                             |
|              |                                                              |
|              | Packet size 100 bytes. Test duration 60 seconds.             |
|              | One ping each 10 seconds. Test is iterated two times.        |
|              | SLA RTT is set to maximum 10 ms.                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This test case can be configured with different:             |
|              |                                                              |
|              |  * packet sizes;                                             |
|              |  * burst sizes;                                              |
|              |  * ping intervals;                                           |
|              |  * test durations;                                           |
|              |  * test iterations.                                          |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably lower RTT is expected, and also normal |
|              | to achieve in balanced L2 environments. However, to cover    |
|              | most configurations, both bare metal and fully virtualized   |
|              | ones, this value should be possible to achieve and           |
|              | acceptable for black box testing. Many real time             |
|              | applications start to suffer badly if the RTT time is higher |
|              | than this. Some may suffer bad also close to this RTT, while |
|              | others may not suffer at all. It is a compromise that may    |
|              | have to be tuned for different configuration purposes.       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Ping_                                                        |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image (cirros-image) needs to be installed     |
|conditions    | into Glance with ping included in it.                        |
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
|              | the SLA. Logs are produced and stored.                       |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Two host VMs are deleted.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test should not PASS if any RTT is above the optional SLA    |
|              | value, or if there is a test case execution problem.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
