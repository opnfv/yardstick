.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2018 Intel Corporation.

***********************************************************
Yardstick Test Case Description: NSB EPC UE SERVICE REQUEST
***********************************************************

+----------------------------------------------------------------------------------+
|NSB EPC UE service request test case                                              |
|                                                                                  |
+--------------+-------------------------------------------------------------------+
|test case id  | tc_epc_{initiator}_service_request_landslide                      |
|              |                                                                   |
|              | * initiator: service request initiator side could be UE (ue) or   |
|              |   Network (nw).                                                   |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|metric        | All metrics provided by Spirent Landslide traffic generator       |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|test purpose  | The Spirent Landslide product provides one box solution which     |
|              | allows to fully emulate all EPC network nodes (DUTs) including    |
|              | mobile users, network host and generate control and data plane    |
|              | traffic.                                                          |
|              |                                                                   |
|              | This test allows to check processing capabilities of DUT under    |
|              | high user connections rate and traffic load for case when UEs     |
|              | initiates service request (UE initiates bearer modification       |
|              | request to provide dedicated bearer for new type of traffic)      |
|              |                                                                   |
|              | It's easy to replace emulated node or multiple nodes in test      |
|              | topology with real node or corresponding vEPC VNF as DUT and      |
|              | check it's processing capabilities under specific test case       |
|              | load conditions.                                                  |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|configuration | The EPC ue service request test cases are listed below:           |
|              |                                                                   |
|              | * tc_epc_ue_service_request_landslide.yaml                        |
|              |                                                                   |
|              | Test duration:                                                    |
|              | * is set as 60sec (specified in test session profile);            |
|              |                                                                   |
|              | Traffic type:                                                     |
|              | * UDP;                                                            |
|              |                                                                   |
|              | Packet sizes:                                                     |
|              | * 512 bytes;                                                      |
|              |                                                                   |
|              | Traffic transaction rate:                                         |
|              | * 5 trans/s.;                                                     |
|              |                                                                   |
|              | Number of mobile subscribers:                                     |
|              | * 20000;                                                          |
|              |                                                                   |
|              | Number of default bearers per subscriber:                         |
|              | * 1;                                                              |
|              |                                                                   |
|              | Number of dedicated bearers per default bearer:                   |
|              | * 1.                                                              |
|              |                                                                   |
|              | TFT settings for dedicated bearers:                               |
|              | * TFT configured to filter TCP traffic (Protocol ID 6)            |
|              |                                                                   |
|              | Modified TFT settings:                                            |
|              | * Create new TFT to filter UDP traffic (Protocol ID 17) from      |
|              |   2002 local port and 2003 remote port;                           |
|              |                                                                   |
|              | Modified QoS settings:                                            |
|              | * Set QCI 5 for dedicated bearers;                                |
|              |                                                                   |
|              | The above fields and values are the main options used for the     |
|              | test case. Other configurable options could be found in test      |
|              | case yaml file. All these options has default values which could  |
|              | be overwritten in test case file.                                 |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|test tool     | Spirent Landslide                                                 |
|              |                                                                   |
|              | The Spirent Landslide is a tool for functional and performance    |
|              | testing of different types of mobile networks. It emulates        |
|              | real-world control and data traffic of mobile subscribers moving  |
|              | through virtualized EPC network.                                  |
|              | Detailed description of Spirent Landslide product could be        |
|              | found here: https://www.spirent.com/Products/Landslide            |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|applicability | This EPC UE SERVICE REQUEST test cases can be configured with     |
|              | different:                                                        |
|              |                                                                   |
|              |  * packet sizes;                                                  |
|              |  * traffic transaction rate;                                      |
|              |  * number of subscribers sessions;                                |
|              |  * number of default bearers per subscriber;                      |
|              |  * number of dedicated bearers per default;                       |
|              |  * subscribers connection rate;                                   |
|              |  * subscribers disconnection rate;                                |
|              |  * dedicated bearers activation timeout;                          |
|              |  * DMF (traffic profile);                                         |
|              |  * enable/disable Fireball DMF threading model that provides      |
|              |    optimized performance;                                         |
|              |  * Starting TFT settings for dedicated bearers;                   |
|              |  * Modified TFT settings for dedicated bearers;                   |
|              |  * Modified QoS settings for dedicated bearers;                   |
|              |                                                                   |
|              | Default values exist.                                             |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|references    | ETSI-NFV-TST001                                                   |
|              |                                                                   |
|              | 3GPP TS 32.455                                                    |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
| pre-test     | * All Spirent Landslide dependencies are installed (detailed      |
| conditions   |   installation steps are described in Readme.rst file for         |
|              |   NSB Spirent Landslide vEPC tests;                               |
|              |                                                                   |
|              | * The pod.yaml file contains all necessary information (TAS VM    |
|              |   ip address, NICs, emulated SUTs and Test Nodes parameters       |
|              |   (names, types, ip addresses, etc.).                             |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|test sequence | description and expected result                                   |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|step 1        | Spirent Landslide components are running on the hosts specified   |
|              | in the pod file.                                                  |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|step 2        | Yardstick is connected with Spirent Landslide Test Automation     |
|              | Server (TAS) by TCL and REST API. The test will resolve the       |
|              | topology and instantiate all emulated EPC network nodes.          |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|step 3        | Test scenarios run, which performs the following steps:           |
|              |                                                                   |
|              | * start emulated EPC network nodes;                               |
|              | * establish subscribers connections to EPC network (default       |
|              |   bearers);                                                       |
|              | * establish specified in test case number of dedicated bearers    |
|              |   per default bearer for each subscriber;                         |
|              | * start run users traffic through EPC network nodes;              |
|              | * During traffic is running, send bearer modification request     |
|              |   after specified in test case timeout;                           |
|              | * disconnect dedicated bearers;                                   |
|              | * disconnect subscribers in the end of the test.                  |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|step 4        | During test run all provided by Spirent Landslide KPI's/metrics   |
|              | are collecting.                                                   |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|step 5        | When test case was completed, this is signalling to yardstick and |
|              | it disconnects from Spirent Landslide.                            |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
|test verdict  | The test case will create the test session in Spirent Landslide   |
|              | with the test case parameters and store the results in the        |
|              | database for benchmarking purposes. The aim is only to collect    |
|              | all the metrics that are provided by Spirent Landslide product    |
|              | for each test specific scenario.                                  |
|              |                                                                   |
+--------------+-------------------------------------------------------------------+
