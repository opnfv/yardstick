.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2018 Intel Corporation.

************************************************
Yardstick Test Case Description: NSB vFW RFC2544
************************************************

+------------------------------------------------------------------------------+
| NSB vFW test for NFVI characterization                                       |
|                                                                              |
+---------------+--------------------------------------------------------------+
| test case id  | tc_{context}_rfc2544_ipv4_1rule_1flow_{pkt_size}_{tg_type}   |
|               |                                                              |
|               | * context = baremetal, heat, heat_external, ovs, sriov       |
|               |             heat_sriov_external contexts;                    |
|               | * tg_type = ixia (context != heat,heat_sriov_external),      |
|               |             trex;                                            |
|               | * pkt_size = 64B - all contexts;                             |
|               |              128B, 256B, 512B, 1024B, 1280B, 1518B -         |
|               |              (context = heat, tg_type = ixia)                |
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
+---------------+--------------------------------------------------------------+
| test purpose  | The VFW RFC2544 tests measure performance characteristics of |
|               | the SUT (multiple ports) and sends UDP bidirectional traffic |
|               | from all TG ports to SampleVNF vFW application. The          |
|               | application forwards received traffic based on rules         |
|               | provided by the user in the TC configuration and default     |
|               | rules created by vFW to send traffic from uplink ports to    |
|               | downlink and voice versa.                                    |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| configuration | The 2 ports RFC2544 test cases are listed below:             |
|               |                                                              |
|               | * tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml        |
|               | * tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_trex.yaml        |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_1024B_ixia.yaml  |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_1280B_ixia.yaml  |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_128B_ixia.yaml   |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_1518B_ixia.yaml  |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_256B_ixia.yaml   |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_512B_ixia.yaml   |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml    |
|               | * tc_heat_external_rfc2544_ipv4_1rule_1flow_64B_trex.yaml    |
|               | * tc_heat_sriov_external_rfc2544_ipv4_1rule_1flow_64B_trex.  |
|               |   yaml                                                       |
|               | * tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex.yaml             |
|               | * tc_ovs_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml              |
|               | * tc_ovs_rfc2544_ipv4_1rule_1flow_64B_trex.yaml              |
|               | * tc_sriov_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml            |
|               | * tc_sriov_rfc2544_ipv4_1rule_1flow_64B_trex.yaml            |
|               |                                                              |
|               | The 4 ports RFC2544 test cases are listed below:             |
|               |                                                              |
|               | * tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_ixia_4port.yaml  |
|               | * tc_tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_trex_4port.   |
|               |   yaml                                                       |
|               | * tc_tc_heat_external_rfc2544_ipv4_1rule_1flow_64B_trex_4    |
|               |   port.yaml                                                  |
|               | * tc_tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_4port.yaml    |
|               |                                                              |
|               | The scale-up RFC2544 test cases are listed below:            |
|               |                                                              |
|               | * tc_tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale-up.yaml |
|               |                                                              |
|               | The scale-out RFC2544 test cases are listed below:           |
|               |                                                              |
|               | * tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale_out.yaml   |
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
|               |  * test duration;                                            |
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
|               | For standalone (SA) SRIOV/OvS test cases the                 |
|               | yardstick-samplevnf image needs to be installed on hosts and |
|               | pod.yaml file must be provided with necessary system, NIC    |
|               | information.                                                 |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test sequence | Description and expected result                              |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 1        | For Baremetal test: The TG (except IXIA) and VNF are started |
|               | on the hosts based on the pod file.                          |
|               |                                                              |
|               | For Heat test: Two host VMs are booted, as Traffic generator |
|               | and VNF(vFW) based on the test flavor. In case of scale-out  |
|               | scenario the multiple VNF VMs will be started.               |
|               |                                                              |
|               | For Heat external test: vFW VM is booted and TG (except IXIA)|
|               | generator is started on the external host based on the pod   |
|               | file. In case of scale-out scenario the multiple VNF VMs     |
|               | will be deployed.                                            |
|               |                                                              |
|               | For Heat SRIOV external test: vFW VM is booted with network  |
|               | interfaces of `direct` type which are mapped to VFs that are |
|               | available to OpenStack. TG (except IXIA) is started on the   |
|               | external host based on the pod file. In case of scale-out    |
|               | scenario the multiple VNF VMs will be deployed.              |
|               |                                                              |
|               | For SRIOV test: VF ports are created on host's PFs specified |
|               | in the TC file and VM is booed using those ports and image   |
|               | provided in the configuration. TG (except IXIA) is started   |
|               | on other host connected to VNF machine based on the pod      |
|               | file. The vFW is started in the booted VM. In case of        |
|               | scale-out scenario the multiple VNF VMs will be created.     |
|               |                                                              |
|               | For OvS test: OvS DPDK switch is started and bridges are     |
|               | created with ports specified in the TC file. DPDK vHost      |
|               | ports are added to corresponding bridge and VM is booed      |
|               | using those ports and image provided in the configuration.   |
|               | TG (except IXIA) is started on other host connected to VNF   |
|               | machine based on the pod file. The vFW is started in the     |
|               | booted VM. In case of scale-out scenario the multiple VNF    |
|               | VMs will be deployed.                                        |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 2        | Yardstick is connected with the TG and VNF by using ssh (in  |
|               | case of IXIA TG is connected via TCL interface). The test    |
|               | will resolve the topology and instantiate all VNFs           |
|               | and TG and collect the KPI's/metrics.                        |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 3        | The TG will send packets to the VNFs. If the number of       |
|               | dropped packets is more than the tolerated loss the line     |
|               | rate or throughput is halved. This is done until the dropped |
|               | packets are within an acceptable tolerated loss.             |
|               |                                                              |
|               | The KPI is the number of packets per second for different    |
|               | packet size with an accepted minimal packet loss for the     |
|               | default configuration.                                       |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| step 4        | In Baremetal test: The test quits the application and unbind |
|               | the DPDK ports.                                              |
|               |                                                              |
|               | In Heat test: All VNF VMs and TG are deleted on test         |
|               | completion.                                                  |
|               |                                                              |
|               | In SRIOV test: The deployed VM with vFW is destroyed on the  |
|               | host and TG (exclude IXIA) is stopped.                       |
|               |                                                              |
|               | In Heat SRIOV test: The deployed VM with vFW is destroyed,   |
|               | VFs are released and TG (exclude IXIA) is stopped.           |
|               |                                                              |
|               | In OvS test: The deployed VM with vFW is destroyed on the    |
|               | host and OvS DPDK switch is stopped and ports are unbinded.  |
|               | The TG (exclude IXIA) is stopped.                            |
|               |                                                              |
+---------------+--------------------------------------------------------------+
| test verdict  | The test case will achieve a Throughput with an accepted     |
|               | minimal tolerated packet loss.                               |
+---------------+--------------------------------------------------------------+

