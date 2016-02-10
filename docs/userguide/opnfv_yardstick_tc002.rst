.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

*************************************
Yardstick Test Case Description TC002
*************************************

.. _cirros-image: https://download.cirros-cloud.net

+-----------------------------------------------------------------------------+
|Network Latency                                                              |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC002_NW LATENCY                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | RTT, Round Trip Time                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To do a basic verification that network latency is within    |
|              | acceptable boundaries when packets travel between hosts      |
|              | located on same or different compute blades.                 |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs and similar shall be stored for comparison reasons and|
|              | product evolution understanding between different OPNFV      |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc002.yaml                             |
|              |                                                              |
|              | Packet size 100 bytes. Total test duration 600 seconds.      |
|              | One ping each 10 seconds. SLA RTT is set to maximum 10 ms.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | ping                                                         |
|              |                                                              |
|              | Ping is normally part of any Linux distribution, hence it    |
|              | doesn't need to be installed. It is also part of the         |
|              | Yardstick Docker image.                                      |
|              | (For example also a Cirros image can be downloaded from      |
|              | cirros-image_, it includes ping)                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Ping man page                                                |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test case can be configured with different packet sizes,     |
|              | burst sizes, ping intervals and test duration.               |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably lower RTT is expected, and             |
|              | also normal to achieve in balanced L2 environments. However, |
|              | to cover most configurations, both bare metal and fully      |
|              | virtualized ones, this value should be possible to achieve   |
|              | and acceptable for black box testing. Many real time         |
|              | applications start to suffer badly if the RTT time is higher |
|              | than this. Some may suffer bad also close to this RTT, while |
|              | others may not suffer at all. It is a compromise that may    |
|              | have to be tuned for different configuration purposes.       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with ping included in it.                                    |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed, as server and client. Ping is       |
|              | invoked and logs are produced and stored.                    |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test should not PASS if any RTT is above the optional SLA    |
|              | value, or if there is a test case execution problem.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
