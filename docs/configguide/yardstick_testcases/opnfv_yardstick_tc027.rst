*************************************
Yardstick Test Case Description TC027
*************************************

.. _ipv6: https://wiki.opnfv.org/ipv6_opnfv_project

+-----------------------------------------------------------------------------+
|IPv6 connectivity between nodes on the tenant network                        |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC002_IPv6 connectivity                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | RTT, Round Trip Time                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To do a basic verification that IPv6 connectivity is within  |
|              | acceptable boundaries when ipv6 packets travel between hosts |
|              | located on same or different compute blades.                 |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs and similar shall be stored for comparison reasons and|
|              | product evolution understanding between different OPNFV      |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc027.yaml                             |
|              |                                                              |
|              | Packet size 56 bytes.                                        |
|              | SLA RTT is set to maximum 10 ms.                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | ping6                                                        |
|              |                                                              |
|              | Ping6 is normally part of Linux distribution, hence it       |
|              | doesn't need to be installed.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | ipv6_                                                        |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test case can be configured with different run step          |
|              | you can run setup, run benchmakr, teardown independently     |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably lower RTT is expected.                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with ping6 included in it.                                   |
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
