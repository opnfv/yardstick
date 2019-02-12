.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2019 Intel Corporation.

***************************************************************
Yardstick Test Case Description: NSB vBNG RFC2544 QoS TEST CASE
***************************************************************

+-----------------------------------------------------------------------------+
|NSB vBNG RFC2544 QoS base line test case without link congestion             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_bng_pppoe_rfc2544_ixia_IMIX_scale_up                      |
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
|              | PPPoE subscriber connections to BNG, runs prioritized traffic|
|              | on maximum throughput on all ports and collects network      |
|              | and PPPoE subscriber metrics.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The BNG QoS RFC2544 test cases are listed below:             |
|              |                                                              |
|              | * tc_bng_pppoe_rfc2544_ixia_IMIX_scale_up.yaml               |
|              |                                                              |
|              | Mentioned test case is a template and number of ports in the |
|              | setup could be passed using cli arguments, e.g:              |
|              |                                                              |
|              | yardstick -d task start --task-args='{vports: 8}' <tc_yaml>  |
|              |                                                              |
|              | By default, vports=2.                                        |
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
+--------------+--------------------------------------------------------------+
|test tool     | IXIA IxNetwork                                               |
|              |                                                              |
|              | IXIA IxNetwork is using to emulates PPPoE sessions, generate |
|              | L2-L3 traffic, analyze traffic flows and collect network     |
|              | metrics during test run.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Mentioned BNG QoS RFC2544 test case can be configured with   |
|              | different:                                                   |
|              |                                                              |
|              |  * Number of PPPoE subscribers sessions;                     |
|              |  * Setup ports number;                                       |
|              |  * IP Priority type;                                         |
|              |  * Packet size;                                              |
|              |  * Enable/disable BGP protocol on core ports;                |
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
|step 1        | Yardstick resolves the topology and connects to IxNetwork    |
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
|              |  6. Create traffic flows between access and core ports       |
|              |     (traffic flows are creating between access-core ports    |
|              |     pairs, traffic is bi-directional);                       |
|              |  7. Configure each traffic flow with specified in traffic    |
|              |     profile options;                                         |
|              |  8. Run traffic with specified in test case file duration;   |
|              |  9. Collect network metrics after traffic was stopped;       |
|              | 10. In case drop percentage rate is higher than expected,    |
|              |     reduce traffic line rate and repeat steps 7-10 again;    |
|              | 11. In case drop percentage rate is as expected or number    |
|              |     of maximum iterations in step 10 achieved, disconnect    |
|              |     PPPoE subscribers and stop traffic;                      |
|              | 12. Stop test.                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | During each iteration interval in the test run, all specified|
|              | metrics are retrieved from IxNetwork and stored in the       |
|              | yardstick dispatcher.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | The vBNG RFC2544 test case will achieve maximum traffic line |
|              | rate with zero packet loss (or other non-zero allowed        |
|              | partial drop rate).                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
