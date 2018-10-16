.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) 2018 Viosoft Corporation.

***********************************************
Yardstick Test Case Description: NSB VPP IPSEC
***********************************************

+---------------------------------------------------------------------------------------------------+
|NSB VPP test for vIPSEC characterization                                                           |
|                                                                                                   |
+--------------+------------------------------------------------------------------------------------+
|test case id  | tc_vpp_{context}_ipsec_{crypto_dev}_{crypto_alg}                                   |
|              |                                                                                    |
|              | * context = baremetal;                                                             |
|              | * crypto_dev = HW_cryptodev or SW_cryptodev;                                       |
|              | * crypto_alg = aes-gcm or cbc-sha1;                                                |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|metric        | * Network Throughput NDR or PDR;                                                   |
|              | * Connections Per Second (CPS)                                                     |
|              | * Latency                                                                          |
|              | * Number of tunnel                                                                 |
|              | * TG Packets Out;                                                                  |
|              | * TG Packets In;                                                                   |
|              | * VNF Packets Out;                                                                 |
|              | * VNF Packets In;                                                                  |
|              | * Dropped packets;                                                                 |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|test purpose  | IPv4 IPsec tunnel mode performance test:                                           |
|              |                                                                                    |
|              | * Finds and reports throughput NDR (Non Drop Rate) with zero packet loss           |
|              |   tolerance or throughput PDR (Partial Drop Rate) with non-zero packet             |
|              |   loss tolerance (LT) expressed in number of packets transmitted.                  |
|              |                                                                                    |
|              | * The IPSEC test cases are implemented to run in baremetal                         |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|configuration | The IPSEC test cases are listed below:                                             |
|              |                                                                                    |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_10GE_trex_scale_up.yaml                        |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_1C_10GE_1518B_trex_corelated_traffic.yaml      |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_1C_10GE_1518B_trex_scale_1000tnl.yaml          |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_1C_10GE_64B_trex_corelated_traffic.yaml        |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_1C_10GE_64B_trex_scale_1000tnl.yaml            |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_1C_10GE_64B_trex_scale.yaml                    |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_2C_10GE_1518B_trex_corelated_traffic.yaml      |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_2C_10GE_1518B_trex_scale_1000tnl.yaml          |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_2C_10GE_64B_trex_corelated_traffic.yaml        |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_2C_10GE_64B_trex_scale_1000tnl.yaml            |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_4C_10GE_1518B_trex_corelated_traffic.yaml      |
|              | * tc_vpp_baremetal_ipsec_sw_aes-gcm_4C_10GE_64B_trex_corelated_traffic.yaml        |
|              | * tc_vpp_baremetal_ipsec_sw_cbc-sha1_1C_10GE_1518B_trex_corelated_traffic.yaml     |
|              | * tc_vpp_baremetal_ipsec_sw_cbc-sha1_1C_10GE_1518B_trex_scale_1000tnl.yaml         |
|              | * tc_vpp_baremetal_ipsec_sw_cbc-sha1_1C_10GE_64B_trex_corelated_traffic.yaml       |
|              | * tc_vpp_baremetal_ipsec_sw_cbc-sha1_1C_10GE_64B_trex_scale_1000tnl.yaml           |
|              |                                                                                    |
|              | Test duration is set as 300sec for each test.                                      |
|              | Packet size set as 64 bytes or higher.                                             |
|              | Number of tunnels set as 1 or higher.                                              |
|              | Number of connections per tunnel set as 1 or higher                                |
|              | These can be configured                                                            |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|test tool     | Vector Packet Processing (VPP)                                                     |
|              | The VPP platform is an extensible framework that provides out-of-the-box           |
|              | production quality switch/router functionality. Its high performance,              |
|              | proven technology, its modularity and flexibility, and rich feature set            |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|applicability | This VPP IPSEC test cases can be configured with different:                        |
|              |                                                                                    |
|              | * packet sizes;                                                                    |
|              | * test durations;                                                                  |
|              | * tolerated loss;                                                                  |
|              | * crypto device type;                                                              |
|              | * number of physical cores;                                                        |
|              | * number of tunnels;                                                               |
|              | * number of connections;                                                           |
|              | * encryption algorithms - integrity algorithm;                                     |
|              |                                                                                    |
|              | Default values exist.                                                              |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|pre-test      | For Baremetal tests cases VPP and Dpdk must be installed in                        |
|conditions    | the hosts where the test is executed. The pod.yaml file must                       |
|              | have the necessary system and NIC information                                      |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|test sequence | description and expected result                                                    |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|step 1        | For Baremetal test: The TG and VNF are started on the hosts                        |
|              | based on the pod file.                                                             |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|step 2        | Yardstick is connected with the TG and VNF by using ssh.                           |
|              | The test will resolve the topology and instantiate the VNF                         |
|              | and TG and collect the KPI's/metrics.                                              |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|step 3        | Test packets are generated by TG on links to DUTs. If the number of                |
|              | dropped packets is more than the tolerated loss the line                           |
|              | rate or throughput is halved. This is done until the dropped                       |
|              | packets are within an acceptable tolerated loss.                                   |
|              |                                                                                    |
|              | The KPI is the number of packets per second for 64 bytes                           |
|              | packet size with an accepted minimal packet loss for the                           |
|              | default configuration.                                                             |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|step 4        | In Baremetal test: The test quits the application and unbind                       |
|              | the dpdk ports.                                                                    |
|              |                                                                                    |
+--------------+------------------------------------------------------------------------------------+
|test verdict  | The test case will achieve a Throughput with an accepted                           |
|              | minimal tolerated packet loss.                                                     |
+--------------+------------------------------------------------------------------------------------+
