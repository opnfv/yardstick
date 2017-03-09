.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC027
*************************************

.. _ipv6: https://wiki.opnfv.org/ipv6_opnfv_project

+-----------------------------------------------------------------------------+
|IPv6 connectivity between nodes on the tenant network                        |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC027_IPv6 connectivity                      |
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
|              | SLA RTT is set to maximum 30 ms.                             |
|              | ipv6 test case can be configured as three independent modules|
|              | (setup, run, teardown). if you only want to setup ipv6       |
|              | testing environment, do some tests as you want, "run_step"   |
|              | of task yaml file should be configured as "setup". if you    |
|              | want to setup and run ping6 testing automatically, "run_step"|
|              | should be configured as "setup, run". and if you have had a  |
|              | environment which has been setup, you only wan to verify the |
|              | connectivity of ipv6 network, "run_step" should be "run". Of |
|              | course, default is that three modules run sequentially.      |
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
|              | you can run setup, run benchmark, teardown independently     |
|              | SLA is optional. The SLA in this test case serves as an      |
|              | example. Considerably lower RTT is expected.                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with ping6 included in it.                                   |
|              |                                                              |
|              | For Brahmaputra, a compass_os_nosdn_ha deploy scenario is    |
|              | need. more installer and more sdn deploy scenario will be    |
|              | supported soon                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | To setup IPV6 testing environment:                           |
|              | 1. disable security group                                    |
|              | 2. create (ipv6, ipv4) router, network and subnet            |
|              | 3. create VRouter, VM1, VM2                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | To run ping6 to verify IPV6 connectivity :                   |
|              | 1. ssh to VM1                                                |
|              | 2. Ping6 to ipv6 router from VM1                             |
|              | 3. Get the result(RTT) and logs are stored                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | To teardown IPV6 testing environment                         |
|              | 1. delete VRouter, VM1, VM2                                  |
|              | 2. delete (ipv6, ipv4) router, network and subnet            |
|              | 3. enable security group                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test should not PASS if any RTT is above the optional SLA    |
|              | value, or if there is a test case execution problem.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
