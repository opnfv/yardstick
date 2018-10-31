.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2018 Intel Corporation.

*********************************************************
Yardstick Test Case Description: NSB EPC SAEGW RELOCATION
*********************************************************

+-----------------------------------------------------------------------------+
|NSB EPC SAEGW throughput with relocation test case                           |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_epc_saegw_tput_relocation_landslide                       |
|              |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | All metrics provided by Spirent Landslide traffic generator  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The Spirent Landslide product provides one box solution which|
|              | allows to fully emulate all EPC network nodes including      |
|              | mobile users, network host and generate control and data     |
|              | plane traffic.                                               |
|              |                                                              |
|              | This test allows to check processing capability of EPC       |
|              | handling large amount of subscribers X2 handovers between    |
|              | different eNBs while UEs are sending traffic.                |
|              |                                                              |
|              | It's easy to replace emulated node or multiple nodes in test |
|              | topology with real node or corresponding vEPC VNF as DUT and |
|              | check it's processing capabilities under specific test case  |
|              | load conditions.                                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The EPC SAEGW throughput with relocation tests are listed    |
|              | below:                                                       |
|              |                                                              |
|              | * tc_epc_saegw_tput_relocation_landslide.yaml                |
|              |                                                              |
|              | Test duration:                                               |
|              |                                                              |
|              | * is set as 60sec (specified in test session profile);       |
|              |                                                              |
|              | Traffic type:                                                |
|              |                                                              |
|              | * UDP;                                                       |
|              |                                                              |
|              | Packet sizes:                                                |
|              |                                                              |
|              | * 512 bytes;                                                 |
|              |                                                              |
|              | Traffic transaction rate:                                    |
|              |                                                              |
|              | * 5 trans/s.;                                                |
|              |                                                              |
|              | Number of mobile subscribers:                                |
|              |                                                              |
|              | * 20000;                                                     |
|              |                                                              |
|              | Number of default bearers per subscriber:                    |
|              |                                                              |
|              | * 1;                                                         |
|              |                                                              |
|              | Handover type:                                               |
|              |                                                              |
|              | * X2 handover;                                               |
|              |                                                              |
|              | Mobility time (timeout after sessions were established after |
|              | which handover will start):                                  |
|              |                                                              |
|              | * 10000ms;                                                   |
|              |                                                              |
|              | Handover start type:                                         |
|              |                                                              |
|              | * When all sessions started;                                 |
|              |                                                              |
|              | Mobility mode:                                               |
|              |                                                              |
|              | * Single handoff;                                            |
|              |                                                              |
|              | Mobility Rate:                                               |
|              |                                                              |
|              | * 120 subscribers/s.                                         |
|              |                                                              |
|              | The above fields and values are the main options used for the|
|              | test case. Other configurable options could be found in test |
|              | session profile yaml file. All these options have default    |
|              | values which can be overwritten in test case file.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Spirent Landslide                                            |
|              |                                                              |
|              | The Spirent Landslide is a tool for functional & performance |
|              | testing of different types of mobile networks. It emulates   |
|              | real-world control and data traffic of mobile subscribers    |
|              | moving through virtualized EPC network.                      |
|              | Detailed description of Spirent Landslide product could be   |
|              | found here: https://www.spirent.com/Products/Landslide       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This EPC UE SERVICE REQUEST test cases can be configured with|
|              | different:                                                   |
|              |                                                              |
|              |  * packet sizes;                                             |
|              |  * traffic transaction rate;                                 |
|              |  * number of subscribers sessions;                           |
|              |  * handover type;                                            |
|              |  * mobility rate;                                            |
|              |  * mobility time;                                            |
|              |  * mobility mode;                                            |
|              |  * handover start condition;                                 |
|              |  * subscribers disconnection rate;                           |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | ETSI-NFV-TST001                                              |
|              |                                                              |
|              | 3GPP TS 32.455                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
| pre-test     | * All Spirent Landslide dependencies are installed (detailed |
| conditions   |   installation steps are described in Chapter 13-            |
|              |   nsb-installation.rst and 14-nsb-operation.rst file for NSB |
|              |   Spirent Landslide vEPC tests;                              |
|              |                                                              |
|              | * The pod.yaml file contains all necessary information       |
|              |   (TAS VM IP address, NICs, emulated SUTs and Test Nodes     |
|              |   parameters (names, types, ip addresses, etc.).             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Spirent Landslide components are running on the hosts        |
|              | specified in the pod file.                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with Spirent Landslide Test           |
|              | Administration Server (TAS) by TCL and REST API. The test    |
|              | will resolve the topology and instantiate all emulated EPC   |
|              | network nodes.                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Test scenarios run, which performs the following steps:      |
|              |                                                              |
|              | * Start emulated EPC network nodes;                          |
|              | * Establish subscribers connections to EPC network (default  |
|              |   bearers);                                                  |
|              | * Start run traffic;                                         |
|              | * After specified in test case mobility timeout, start       |
|              |   handover process on specified mobility rate;               |
|              | * Disconnect subscribers at the end of the test.             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | During test run, all the metrics provided by Spirent         |
|              | Landslide are stored in the yardstick dispatcher.            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | The test case will create the test session in Spirent        |
|              | Landslide with the test case parameters and store the        |
|              | results in the database for benchmarking purposes. The aim   |
|              | is only to collect all the metrics that are provided by      |
|              | Spirent Landslide product for each test specific scenario.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
