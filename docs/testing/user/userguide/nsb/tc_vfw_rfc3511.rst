.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2018 Intel Corporation.

*******************************************************
Yardstick Test Case Description: NSB vFW RFC3511 (HTTP)
*******************************************************

+------------------------------------------------------------------------------+
| NSB vFW test for NFVI characterization based on RFC3511 and IXIA             |
|                                                                              |
+---------------+--------------------------------------------------------------+
| test case id  | tc_{context}_http_ixload_{http_size}_Requests-65000_{type}   |
|               |                                                              |
|               | * context = baremetal, heat_external                         |
|               | * http_size = 1b, 4k, 64k, 256k, 512k, 1024k payload size    |
|               | * type = Concurrency, Connections, Throughput                |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| metric        | * HTTP Total Throughput (Kbps);                              |
|               | * HTTP Simulated Users;                                      |
|               | * HTTP Concurrent Connections;                               |
|               | * HTTP Connection Rate;                                      |
|               | * HTTP Transaction Rate                                      |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test purpose  | The vFW RFC3511 tests measure performance characteristics of |
|               | the SUT by sending the HTTP traffic from uplink to downlink  |
|               | TG ports through vFW VNF. The application forwards received  |
|               | traffic based on rules provided by the user in the TC        |
|               | configuration and default rules created by vFW to send       |
|               | traffic from uplink ports to downlink and voice versa.       |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| configuration | The 2 ports RFC3511 test cases are listed below:             |
|               |                                                              |
|               | * tc_baremetal_http_ixload_1024k_Requests-65000              |
|               |   _Concurrency.yaml                                          |
|               | * tc_baremetal_http_ixload_1b_Requests-65000                 |
|               |   _Concurrency.yaml                                          |
|               | * tc_baremetal_http_ixload_256k_Requests-65000               |
|               |   _Concurrency.yaml                                          |
|               | * tc_baremetal_http_ixload_4k_Requests-65000                 |
|               |   _Concurrency.yaml                                          |
|               | * tc_baremetal_http_ixload_512k_Requests-65000               |
|               |   _Concurrency.yaml                                          |
|               | * tc_baremetal_http_ixload_64k_Requests-65000                |
|               |   _Concurrency.yaml                                          |
|               | * tc_heat_external_http_ixload_1b_Requests-10Gbps            |
|               |   _Throughput.yaml                                           |
|               | * tc_heat_external_http_ixload_1b_Requests-65000             |
|               |   _Concurrency.yaml                                          |
|               | * tc_heat_external_http_ixload_1b_Requests-65000             |
|               |   _Connections.yaml                                          |
|               |                                                              |
|               | The 4 ports RFC3511 test cases are listed below:             |
|               |                                                              |
|               | * tc_baremetal_http_ixload_1b_Requests-65000                 |
|               |   _Concurrency_4port.yaml                                    |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test tool     | The vFW is a DPDK application that performs basic filtering  |
|               | for malformed packets and dynamic packet filtering of        |
|               | incoming packets using the connection tracker library.       |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| applicability | The vFW RFC3511 test cases can be configured with different: |
|               |                                                              |
|               |  * http payload sizes;                                       |
|               |  * traffic flows;                                            |
|               |  * rules;                                                    |
|               |                                                              |
|               | Default values exist.                                        |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| pre-test      | For OpenStack test case image (yardstick-samplevnf) needs    |
| conditions    | to be installed into Glance with vFW and DPDK included in    |
|               | it (NSB install).                                            |
|               |                                                              |
|               | For Baremetal tests cases vFW and DPDK must be installed on  |
|               | the hosts where the test is executed. The pod.yaml file must |
|               | have the necessary system and NIC information.               |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test sequence | Description and expected result                              |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 1        | For Baremetal test: The vFW VNF is started on the hosts      |
|               | based on the pod file.                                       |
|               |                                                              |
|               | For Heat external test: The vFW VM are deployed and booted.  |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 2        | Yardstick is connected with the TG (IxLoad) via TCL and VNF  |
|               | by using ssh. The test will resolve the topology and         |
|               | instantiate all VNFs and TG and collect the KPI's/metrics.   |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 3        | The TG simulates HTTP traffic based on selected type of TC.  |
|               |                                                              |
|               | Concurrency:                                                 |
|               |   The TC attempts to simulate some number of human users.    |
|               |   The simulated users are gradually brought online until 64K |
|               |   users is met (the Ramp-Up phase), then taken offline (the  |
|               |   Ramp Down phase).                                          |
|               |                                                              |
|               | Connections:                                                 |
|               |   The TC creates some number of HTTP connections per second. |
|               |   It will attempt to generate the 64K of HTTP connections    |
|               |   per second.                                                |
|               |                                                              |
|               | Throughput:                                                  |
|               |   TC simultaneously transmits and receives TCP payload       |
|               |   (bytes) at a certain rate measured in Megabits per second  |
|               |   (Mbps), Kilobits per second (Kbps), or Gigabits per        |
|               |   second. The 10 Gbits is default throughput.                |
|               |                                                              |
|               | At the end of the TC, the KPIs are collected and stored      |
|               | (depends on the selected dispatcher).                        |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 4        | In Baremetal test: The test quits the application and        |
|               | unbinds the DPDK ports.                                      |
|               |                                                              |
|               | In Heat test: All VNF VMs are deleted and connections to TG  |
|               | are terminated.                                              |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test verdict  | The test case will try to achieve the configured HTTP        |
|               | Concurrency/Throughput/Connections.                          |
+---------------+--------------------------------------------------------------+

