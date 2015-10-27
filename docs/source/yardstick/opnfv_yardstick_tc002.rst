.. image:: ../../etc/opnfv-logo.png
  :height: 40
  :width: 200
  :alt: OPNFV
  :align: left

*************************************
Yardstick Test Case Description TC002
*************************************

+-----------------------------------------------------------------------------+
|Network Latency                                                              |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC002_NW LATENCY                             |
+--------------+--------------------------------------------------------------+
|metric        | RTT, Round Trip Time                                         |
+--------------+--------------------------------------------------------------+
|test purpose  | To do a basic verification that network latency is within    |
|              | acceptable boundaries when packets travel between hosts      |
|              | located on same or different compute blades.                 |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs and similar shall be stored for comparison reasons and|
|              | product evolution understanding between different OPNFV      |
|              | versions and/or configurations.                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc002.yaml                             |
|              |                                                              |
|              | - Packet size 100 bytes                                      |
|              | - Total test duration 600 seconds                            |
|              | - One ping each 10 seconds                                   |
|              | - SLA maximum RTT 10 ms                                      |
|              | - Distribution policy for client and server to run on        |
|              |   different HW                                               |
+--------------+--------------------------------------------------------------+
|test tool     | ping                                                         |
|              |                                                              |
|              | Ping is normally part of any Linux distribution, hence it    |
|              | doesn't need to be installed. It is also part of the         |
|              | Yardstick Docker image.                                      |
|              | (For example also a Cirros image can be downloaded from      |
|              | https://download.cirros-cloud.net, it includes ping)         |
+--------------+--------------------------------------------------------------+
|references    | Ping man page                                                |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test case can be configured with different packet sizes,     |
|              | burst sizes, ping interval, test duration, VM distribution   |
|              | policy and SLA (optional). SLA in this test case serves as an|
|              | example. Considerably lower RTT is expected, and             |
|              | also normal to achieve in balanced L2 environments. However, |
|              | to cover most configurations, both bare metal and fully      |
|              | virtualized ones, this value should be possible to achieve   |
|              | and acceptable for black box testing. Many real time         |
|              | applications start to suffer badly if the RTT time is higher |
|              | than this. Some may suffer badly also close to this RTT,     |
|              | while others may not suffer at all. It is a compromise that  |
|              | may have to be tuned for different configuration purposes.   |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with ping included in it.                                    |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
+--------------+------+----------------------------------+--------------------+
|test sequence | step | description                      | result             |
|              +------+----------------------------------+--------------------+
|              |  1   | The hosts are installed, as      | Logs are stored    |
|              |      | server and client. Ping is       |                    |
|              |      | invoked and logs are produced    |                    |
|              |      | and stored.                      |                    |
+--------------+------+----------------------------------+--------------------+
|test verdict  | Test should not PASS if any RTT is above the optional SLA    |
|              | value, or if there is a test case execution problem.         |
+--------------+--------------------------------------------------------------+



