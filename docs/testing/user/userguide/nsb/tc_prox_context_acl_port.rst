.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2017 Intel Corporation.

*********************************************
Yardstick Test Case Description: NSB PROX ACL
*********************************************

+-----------------------------------------------------------------------------+
|NSB PROX test for NFVI characterization                                      |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | tc_prox_{context}_acl-{port_num}                             |
|              |                                                              |
|              | * context = baremetal or heat_context;                       |
|              | * port_num = 2 or 4;                                         |
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
|test purpose  | This test allows to measure how well the SUT can exploit     |
|              | structures in the list of ACL rules.                         |
|              | The ACL rules are matched against a 7-tuple of the input     |
|              | packet: the regular 5-tuple and two VLAN tags.               |
|              | The rules in the rule set allow the packet to be forwarded   |
|              | and the rule set contains a default "match all" rule.        |
|              |                                                              |
|              | The KPI is measured with the rule set that has a moderate    |
|              | number of rules with moderate similarity between the rules & |
|              | the fraction of rules that were used.                        |
|              |                                                              |
|              | The ACL test cases are implemented to run in  baremetal      |
|              | and heat context for 2 port and 4 port configuration.        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | The ACL test cases are listed below:                         |
|              |                                                              |
|              | * tc_prox_baremetal_acl-2.yaml                               |
|              | * tc_prox_baremetal_acl-4.yaml                               |
|              | * tc_prox_heat_context_acl-2.yaml                            |
|              | * tc_prox_heat_context_acl-4.yaml                            |
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
|applicability | This PROX ACL test cases can be configured with different:   |
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
|              | and VNF(ACL workload) based on the test flavor.              |
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
|              | The KPI is the number of packets per second for 64 bytes     |
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

