.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC081
*************************************

.. _cirros-image: https://download.cirros-cloud.net
.. _Ping: https://linux.die.net/man/8/ping

+-----------------------------------------------------------------------------+
|Network Latency                                                              |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC081_NETWORK_LATENCY_BETWEEN_CONTAINER_AND_ |
|              | VM                                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | RTT (Round Trip Time)                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC081 is to do a basic verification that      |
|              | network latency is within acceptable boundaries when packets |
|              | travel between a containers and a VM.                        |
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
|              | Yardstick Docker image. (For example also a Cirros image can |
|              | be downloaded from cirros-image_, it includes ping)          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test topology | Ping packets (ICMP protocol's mandatory ECHO_REQUEST         |
|              | datagram) are sent from host container to target vm to       |
|              | elicit ICMP ECHO_RESPONSE.                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc081.yaml                             |
|              |                                                              |
|              | Packet size 200 bytes. Test duration 60 seconds.             |
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
|usability     | This test case should be run in Kunernetes environment.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Ping_                                                        |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case Docker image (openretriever/yardstick) needs   |
|conditions    | to be pulled into Kubernetes environment.                    |
|              | The VM image (cirros-image) needs to be installed into       |
|              | Glance with ping included in it.                             |
|              |                                                              |
|              | No further requirements have been identified.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | A containers is booted, as server and a VM is booted as      |
|              | client.                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the server container by using    |
|              | ssh. 'ping_benchmark' bash script is copied from Jump Host   |
|              | to the server container via the ssh tunnel.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Ping is invoked. Ping packets are sent from server container |
|              | to client VM. RTT results are calculated and checked against |
|              | the SLA. Logs are produced and stored.                       |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The container and VM are deleted.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test should not PASS if any RTT is above the optional SLA    |
|              | value, or if there is a test case execution problem.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
