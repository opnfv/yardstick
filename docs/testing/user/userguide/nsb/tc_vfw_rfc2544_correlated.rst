.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2018 Intel Corporation.

*************************************************************
Yardstick Test Case Description: NSB vFW RFC2544 (correlated)
*************************************************************

+------------------------------------------------------------------------------+
| NSB vFW test for NFVI characterization using correlated traffic              |
|                                                                              |
+---------------+--------------------------------------------------------------+
| test case id  | tc_{context}_rfc2544_ipv4_1rule_1flow_64B_trex_corelated     |
|               |                                                              |
|               | * context = baremetal, heat                                  |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| metric        | * Network Throughput;                                        |
|               | * TG Packets Out;                                            |
|               | * TG Packets In;                                             |
|               | * TG Latency;                                                |
|               | * VNF Packets Out;                                           |
|               | * VNF Packets In;                                            |
|               | * VNF Packets Fwd;                                           |
|               | * Dropped packets;                                           |
|               |                                                              |
|               | NOTE: For correlated TCs the TG metrics are available on     |
|               | uplink ports.                                                |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test purpose  | The VFW RFC2544 correlated tests measure performance         |
|               | characteristics of the SUT (multiple ports) and sends UDP    |
|               | traffic from uplink TG ports to SampleVNF vFW application.   |
|               | The application forwards received traffic from uplink ports  |
|               | to downlink ports based on rules provided by the user in the |
|               | TC configuration and default rules created by vFW. The VNF   |
|               | downlink traffic is received by another UDPReplay VNF and it |
|               | is mirrored back to the VNF on the same port. Finally, the   |
|               | traffic is received back to the TG uplink port.              |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| configuration | The 2 ports RFC2544 correlated test cases are listed below:  |
|               |                                                              |
|               | * tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_trex_corelated   |
|               |   _traffic.yaml                                              |
|               |                                                              |
|               | Multiple VNF (2, 4, 10) RFC2544 correlated test cases are    |
|               | listed below:                                                |
|               |                                                              |
|               | * tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_correlated       |
|               |   _scale_10.yaml                                             |
|               | * tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_correlated_scale |
|               |   _2.yaml                                                    |
|               | * tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_correlated_scale |
|               |   _4.yaml                                                    |
|               |                                                              |
|               | The scale-out RFC2544 test cases are listed below:           |
|               |                                                              |
|               | * tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_correlated_scale |
|               |   _out.yaml                                                  |
|               |                                                              |
|               | Test duration is set as 30 sec for each test and default     |
|               | number of rules are applied. These can be configured         |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test tool     | The vFW is a DPDK application that performs basic filtering  |
|               | for malformed packets and dynamic packet filtering of        |
|               | incoming packets using the connection tracker library.       |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| applicability | The vFW RFC2544 test cases can be configured with different: |
|               |                                                              |
|               |  * packet sizes;                                             |
|               |  * test duration;                                           |
|               |  * tolerated loss;                                           |
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
| step 1        | For Baremetal test: The TG (except IXIA), vFW and UDPReplay  |
|               | VNFs are started on the hosts based on the pod file.         |
|               |                                                              |
|               | For Heat test: Three host VMs are booted, as Traffic         |
|               | generator, vFW and UDPReplay VNF(vFW) based on the test      |
|               | flavor. In case of scale-out scenario the multiple vFW VNF   |
|               | VMs will be started.                                         |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 2        | Yardstick is connected with the TG, vFW and UDPReplay VNF by |
|               | using ssh (in case of IXIA TG is connected via TCL           |
|               | interface). The test will resolve the topology and           |
|               | instantiate all VNFs and TG and collect the KPI's/metrics.   |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 3        | The TG will send packets to the VNFs. If the number of       |
|               | dropped packets is more than the tolerated loss the line     |
|               | rate or throughput is halved. This is done until the dropped |
|               | packets are within an acceptable tolerated loss.             |
|               |                                                              |
|               | The KPI is the number of packets per second for 64B packet   |
|               | size with an accepted minimal packet loss for the default    |
|               | configuration.                                               |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 4        | In Baremetal test: The test quits the application and unbind |
|               | the DPDK ports.                                              |
|               |                                                              |
|               | In Heat test: All VNF VMs and TG are deleted on test         |
|               | completion.                                                  |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test verdict  | The test case will achieve a Throughput with an accepted     |
|               | minimal tolerated packet loss.                               |
+---------------+--------------------------------------------------------------+

