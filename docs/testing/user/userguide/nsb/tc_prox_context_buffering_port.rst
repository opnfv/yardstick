.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2017 Intel Corporation.

**********************************************************
Yardstick Test Case Description: NSB PROX Packet Buffering
**********************************************************

+-----------------------------------------------------------------------------+
|NSB PROX test for NFVI characterization                                      |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_prox_{context}_buffering-{port_num}                       |
|              |                                                              |
|              | * context = baremetal or heat_context                        |
|              | * port_num = 1, 2 or 4                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | * Network Throughput;                                        |
|              | * TG Packets Out;                                            |
|              | * TG Packets In;                                             |
|              | * VNF Packets Out;                                           |
|              | * VNF Packets In;                                            |
|              | * Dropped packets;                                           |
|              | * CPU Utilization;                                           |
|              | * Latency;                                                   |
+--------------+--------------------------------------------------------------+
|test purpose  | This test measures the impact of the condition when packets  |
|              | get buffered, thus they stay in memory for the extended      |
|              | period of time, 125ms in this case.                          |
|              |                                                              |
|              | The Packet Buffering test cases are implemented to run in    |
|              | baremetal and heat context.                                  |
|              |                                                              |
|              | The test cases are implemented for baremetal and heat        |
|              | context for 1, 2 port and 4 port configuration.              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The Packet Buffering test cases are listed below:            |
|              |                                                              |
|              | * tc_prox_baremetal_buffering-1.yaml                         |
|              | * tc_prox_heat_context_buffering-1.yaml                      |
|              | * tc_prox_baremetal_buffering-2.yaml                               |
|              | * tc_prox_baremetal_buffering-4.yaml                               |
|              | * tc_prox_heat_context_buffering-2.yaml                            |
|              | * tc_prox_heat_context_buffering-4.yaml                            |
|              |                                                              |
|              | Test duration is set as 8000sec for each test.               |
|              | Packet size set as 64, 128, 256, 512, 1024, 1280, 1518 bytes |
|              | This is set in the traffic profile and can be reconfigured   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | PROX                                                         |
|              | PROX is a DPDK application that can simulate VNF workloads   |
|              | and can generate traffic and used for NFVI characterization  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | The PROX Packet Buffering test cases can be configured with  |
|              |  different:                                                  |
|              |                                                              |
|              |  * packet sizes;                                             |
|              |  * test durations;                                           |
|              |  * tolerated loss;                                           |
|              |  * Interface speed 10,25 and 40 Gbps interface are supported |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | For Openstack test case image (yardstick-samplevnfs) needs   |
|conditions    | to be installed into Glance with Prox and Dpdk included in   |
|              | it. The test need multi-queue enabled in Glance image.       |
|              | Please Ensure                                                |
|              | 1. Glance image created with hw:vif_multiqueue_enabled: true |
|              | 2. SUT and VNF VMs support 32 VCPUs                          |
|              |                                                              |
|              | For Baremetal tests cases Prox and Dpdk must be installed in |
|              | the hosts where the test is executed. The pod.yaml file must |
|              | have the necessary system and NIC information                |
|              | Please Ensure                                                |
|              | 1. SUT and VNF support 32 CPUs                               |
|              | 2. "/opt/nsb-bin" contains "prox", "dpdk-devbind.py" and     |
|              |    "collectd"
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | For Baremetal test: The TG and VNF are started on the hosts  |
|              | based on the pod file.                                       |
|              |                                                              |
|              | For Heat test: Two host VMs are booted, as Traffic generator |
|              | and VNF(Packet Buffering workload) based on the test flavor. |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the TG and VNF by using ssh.     |
|              | The test will resolve the topology and instantiate the VNF   |
|              | and TG and collect the KPI's/metrics.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | The TG will send packets to the VNF. If the number of        |
|              | dropped packets is more than the tolerated loss the line     |
|              | rate or throughput is halved. This is done until the dropped |
|              | packets are within an acceptable tolerated loss.             |
|              |                                                              |
|              | The KPI in this test is the maximum number of packets that   |
|              | can be forwarded given the requirement that the latency of   |
|              | each packet is at least 125 millisecond.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | In Baremetal test: The test quits the application and unbind |
|              | the dpdk ports.                                              |
|              |                                                              |
|              | In Heat test: Two host VMs are deleted on test completion.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | The test case will achieve a Throughput with an accepted     |
|              | minimal tolerated packet loss.                               |
+--------------+--------------------------------------------------------------+

