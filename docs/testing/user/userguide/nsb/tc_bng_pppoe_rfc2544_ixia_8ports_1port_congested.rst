.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2019 Intel Corporation.

***************************************************************
Yardstick Test Case Description: NSB vBNG RFC2544 QoS TEST CASE
***************************************************************

+-----------------------------------------------------------------------------+
|NSB vBNG RFC2544 QoS base line test case with link congestion                |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_bng_pppoe_rfc2544_ixia_8ports_1port_congested_IMIX        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
| metric       | Network metrics:                                             |
|              | * TxThroughput                                               |
|              | * RxThroughput                                               |
|              | * TG packets in                                              |
|              | * TG packets out                                             |
|              | * Max Latency                                                |
|              | * Min Latency                                                |
|              | * Average Latency                                            |
|              | * Packets drop percentage                                    |
|              |                                                              |
|              | PPPoE subscribers metrics:                                   |
|              | * Sessions up                                                |
|              | * Sessions down                                              |
|              | * Sessions Not Started                                       |
|              | * Sessions Total                                             |
|              |                                                              |
|              | NOTE: the same network metrics list are collecting:          |
|              | * summary for all ports                                      |
|              | * per port                                                   |
|              | * per priority flows summary on all ports                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test allows to measure performance of BNG network device|
|              | according to RFC2544 testing methodology. Test case creates  |
|              | PPPoE subscribers connections to BNG, run prioritized traffic|
|              | causing congestion of access port (port xe0) and collects    |
|              | network and PPPoE subscribers metrics.                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The BNG QoS RFC2544 test cases are listed below:             |
|              |                                                              |
|              | * tc_bng_pppoe_rfc2544_ixia_8ports_1port_congested_IMIX.yaml |
|              |                                                              |
|              | Number of ports:                                             |
|              | * 8 ports                                                    |
|              |                                                              |
|              | Test duration:                                               |
|              | * set as 30sec;                                              |
|              |                                                              |
|              | Traffic type:                                                |
|              | * IPv4;                                                      |
|              |                                                              |
|              | Packet sizes:                                                |
|              | * IMIX. The following default IMIX distribution is using:    |
|              |                                                              |
|              |   uplink: 70B - 33%, 940B - 33%, 1470B - 34%                 |
|              |   downlink: 68B - 3%, 932B - 1%, 1470B - 96%                 |
|              |                                                              |
|              | VLAN settings:                                               |
|              | * QinQ on access ports;                                      |
|              | * VLAN on core ports;                                        |
|              |                                                              |
|              | Number of PPPoE subscribers:                                 |
|              | * 4000 per access port;                                      |
|              | * 1000 per SVLAN;                                            |
|              |                                                              |
|              | Default ToS bits settings:                                   |
|              | * 0 - (000) Routine                                          |
|              | * 4 - (100) Flash Override                                   |
|              | * 7 - (111) Network Control.                                 |
|              |                                                              |
|              | The above fields are the main options used for the test case |
|              | and could be configured using cli options on test run or     |
|              | directly in test case yaml file.                             |
|              |                                                              |
|              | NOTE: that only parameter that can't be changed is ports     |
|              | number. To run the test with another number of ports         |
|              | traffic profile should be updated.                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | IXIA IxNetwork                                               |
|              |                                                              |
|              | IXIA IxNetwork is using to emulates PPPoE sessions, generate |
|              | L2-L3 traffic, analyze traffic flows and collect network     |
|              | metrics during test run.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Mentioned BNG QoS RFC2544 test cases can be configured with  |
|              | different:                                                   |
|              |                                                              |
|              |  * Number of PPPoE subscribers sessions;                     |
|              |  * IP Priority type;                                         |
|              |  * Packet size;                                              |
|              |  * enable/disable BGP protocol on core ports;                |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | RFC2544                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
| pre-test     | 1. BNG is up and running and has configured:                 |
| conditions   |   * access ports with QinQ tagging;                          |
|              |   * core ports with configured IP addresses and VLAN;        |
|              |   * PPPoE subscribers authorization settings (no auth or     |
|              |     Radius server, PAP auth protocol);                       |
|              |   * QoS settings;                                            |
|              |                                                              |
|              | 2. IxNetwork API server is running on specified in pod.yaml  |
|              |    file TCL port;                                            |
|              |                                                              |
|              | 3. BNG ports are connected to IXIA ports (IXIA uplink        |
|              |    ports are connected to BNG access ports and IXIA          |
|              |    downlink ports are connected to BNG core ports;           |
|              |                                                              |
|              | 4. The pod.yaml file contains all necessary information      |
|              |    (BNG access and core ports settings, core ports IP        |
|              |    address, NICs, IxNetwork TCL port, IXIA uplink/downlink   |
|              |    ports, etc).                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Yardstick resolve the topology and connects to IxNetwork     |
|              | API server by TCL.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Test scenarios run, which performs the following steps:      |
|              |                                                              |
|              |  1. Create access network topologies (this topologies are    |
|              |     based on IXIA ports which are connected to BNG access    |
|              |     ports);                                                  |
|              |  2. Configure access network topologies with multiple device |
|              |     groups. Each device group represents single SVLAN with   |
|              |     PPPoE subscribers sessions (number of created on port    |
|              |     SVLANs and subscribers depends on specified if test case |
|              |     file options);                                           |
|              |  3. Create core network topologies (this topologies are      |
|              |     based on IXIA ports which are connected to BNG core      |
|              |     ports);                                                  |
|              |  4. Configure core network topologies with single device     |
|              |     group which represents one connection with configured    |
|              |     VLAN and BGP protocol;                                   |
|              |  5. Establish PPPoE subscribers connections to BNG;          |
|              |  6. Create traffic flows between access and core ports.      |
|              |     While test covers case with access port congestion,      |
|              |     flows between ports will be created in the following     |
|              |     way: traffic from two core ports are going to one access |
|              |     port causing port congestion and traffic from other two  |
|              |     core ports is splitting between remaining three access   |
|              |     ports;                                                   |
|              |  7. Configure each traffic flow with specified in traffic    |
|              |     profile options;                                         |
|              |  8. Run traffic with specified in test case file duration;   |
|              |  9. Collect network metrics after traffic was stopped;       |
|              | 10. Measure drop percentage rate of different priority       |
|              |     packets on congested port. Expected that all high and    |
|              |     medium priority packets was forwarded and only low       |
|              |     priority packets has drops.                              |
|              | 11. Disconnect PPPoE subscribers and stop test.              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | During test run, in the end of each iteration all specified  |
|              | in the document metrics are retrieved from IxNetwork and     |
|              | stored in the yardstick dispatcher.                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | The test case is successful if all high and medium priority  |
|              | packets on congested port was forwarded and only low         |
|              | priority packets has drops.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
