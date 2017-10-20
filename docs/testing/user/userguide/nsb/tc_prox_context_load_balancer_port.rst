.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2017 Intel Corporation.

*******************************************************
Yardstick Test Case Description: NSB PROX Load Balancer
*******************************************************

+-----------------------------------------------------------------------------+
|NSB PROX test for NFVI characterization                                      |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_prox_{context}_lb-{port_num}                              |
|              |                                                              |
|              | * context = baremetal or heat_context                        |
|              | * port_num = 4                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | * Network Throughput;                                        |
|              | * TG Packets Out;                                            |
|              | * TG Packets In;                                             |
|              | * VNF Packets Out;                                           |
|              | * VNF Packets In;                                            |
|              | * Dropped packets;                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The applciation transmits packets on one port and revieves   |
|              | them on 4 ports.                                             |
|              | The conventional 5-tuple is used in this test as it requires |
|              | some extraction steps and allows defining enough distinct    |
|              | values to find the performance limits.                       |
|              |                                                              |
|              | The load is increased (adding more ports if needed) while    |
|              | packets are load balanced using a hash table of 8M entries   |
|              |                                                              |
|              | The number of packets per second that can be forwarded       |
|              | determines the KPI. The default packet size is 64 bytes.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The Load Balancer test cases are listed below:               |
|              |                                                              |
|              | * tc_prox_baremetal_lb-4.yaml                                |
|              | * tc_prox_heat_context_lb-4.yaml                             |
|              |                                                              |
|              | Test duration is set as 300sec for each test.                |
|              | Packet size set as 64 bytes in traffic profile.              |
|              | These can be configured                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | PROX                                                         |
|              | PROX is a DPDK application that can simulate VNF workloads   |
|              | and can generate traffic and used for NFVI characterization  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | The PROX Load Balancer test cases can be configured with     |
|              |  different:                                                  |
|              |                                                              |
|              |  * packet sizes;                                             |
|              |  * test durations;                                           |
|              |  * tolerated loss;                                           |
|              |                                                              |
|              | Default values exist.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | For Openstack test case image (yardstick-samplevnfs) needs   |
|conditions    | to be installed into Glance with Prox and Dpdk included in   |
|              | it. The test need multi-queue enabled in Glance image.       |
|              |                                                              |
|              | For Baremetal tests cases Prox and Dpdk must be installed in |
|              | the hosts where the test is executed. The pod.yaml file must |
|              | have the necessary system and NIC information                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | For Baremetal test: The TG and VNF are started on the hosts  |
|              | based on the pod file.                                       |
|              |                                                              |
|              | For Heat test: Two host VMs are booted, as Traffic generator |
|              | and VNF(Load Balancer workload) based on the test flavor.    |
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
|              | The KPI is the number of packets per second for 78 bytes     |
|              | packet size with an accepted minimal packet loss for the     |
|              | default configuration.                                       |
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

