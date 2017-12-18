.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC084
*************************************

+-----------------------------------------------------------------------------+
|SDN Controller resilience in non-HA configuration                            |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC084: SDN controller resilience in          |
|              | non-HA configuration                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test validates SDN controller node high availability by |
|              | verifying there is no impact on the data plane connectivity  |
|              | when a SDN controller is shutdown in non-HA configuration.   |
|              | i.e. all existing configured network services DHCP, ARP, L2, |
|              | L3, L3VPN, Security Groups should continue to operate        |
|              | between the existing VMs while SDN controller is rebooting.  |
|              | The test also validates the new network service operations   |
|              | (creating a new VM in the existing L2/L3 network or in a new |
|              | network...etc) are operational after the SDN controller      |
|              | recovers from the failure                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case shutsdown the SDN controller service running  |
|              | on the OpenStack controller node, then checks if already     |
|              | configured DHCP/ARP/L2/L3/L3VPN SNAT connectivity is not     |
|              | impacted in the existing VMs and system is able to execute   |
|              | new virtual network operations once the opendaylight service |
|              | is fully recovered                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called “kill-process” is      |
|              | needed.This attacker includes three parameters:              |
|              | 1) fault_type: which is used for finding the attacker’s      |
|              | scripts. It should be set to 'kill-process' in this test     |
|              | 2) process_name: should be set to sdn controller process     |
|              | 3) host: which is the name of a control node where           |
|              | opendaylight process is running                              |
|              |                                                              |
|              | e.g. -fault_type: “kill-process”                             |
|              |      -process_name: “opendaylight-karaf” (TBD)               |
|              |      -host: node1                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, the following monitors are needed         |
|              | 1. "ping_same_network_l2": monitor ping traffic between      |
|              |    the VMs in same neutron network                           |
|              | 2. "ping_other_network_l3": monitor ping traffic between     |
|              |    the VMs in different neutron networks attached to same    |
|              |    neutron router                                            |
|              | 3. "ping_external_snat": monitor ping traffic from VMs to    |
|              |    external destinations (e.g. google.com)                   |
|              | NOTE: the above monitors need to be developed as part of     |
|              | as part of this test case implementation                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|operations    | In this test case, the following operations are needed:      |
|              | 1)"nova-create-instance-in_network": create a VM instance    |
|              | in one of the existing neutron network.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are two metrics:                    | 
|              | 1)process_recover_time: which indicates the maximun          |
|              |   time (seconds) from the process being killed to recovered  |
|              | 2)ping_packet_drop: TBD                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Developed by the project. Please see folder:                 |
|              | "yardstick/benchmark/scenarios/availability/ha_tools"        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | TBD                                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              | 1) test case file: opnfv_yardstick_tc084.yaml                |
|              |    -Attackers: see above “attackers” discription             |
|              |    -waiting_time: which is the time (seconds) from the       |
|              |     process being killed to stoping monitors the monitors    |
|              |    -Monitors: see above “monitors” discription               |
|              |    -SLA: see above “metrics” discription                     |
|              | 2)POD file: pod.yaml The POD configuration should record on  |
|              |   pod.yaml first. the “host” item in this test case will use |
|              |   the node name in the pod.yaml.                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    | 1)The OpenStack Cluster is setup with SDN controller         |
|              | 2)One or more neutron networks are created with two or       |
|              |   more VMs attached to each of the neutron networks.         |
|              | 3)The neutron networks are attached to a neutron router      |
|              |   which is attached to a L3VPN based external network        |
|              |   towards DCGW.                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | start ip connectivity monitors:                              |
|              | 1. Check the L2 connectivity between the VMs in the same     |
|              |    neutron network.                                          |
|              | 2. Check the L3 connectivity between VMs in different        |
|              |    neutron networks attached to neutron router.              |
|              | 3. Check the L3VPN SNAT connectivity from the VMs.           |
|              | each monitor will run with independently process             |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | determine the VIM controller node on which sdn controller    |
|              | service is running                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | start attacker:                                              |
|              | SSH connect to the VIM node and kill sdn controller process  |
|              |                                                              |
|              | Result: the sdn controller service will be shutdown          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | stop ip connectivity monitors after a period of time         |
|              | specified by “waiting_time”                                  |
|              |                                                              |
|              | Result: The monitor info will be aggregated                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | verify the ip connectivity monitor result                    |
|              |                                                              |
|              | Result: ip connectivity monitor should not have any packet   |
|              | drop failures reported                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | verify process_recover_time, which indicates the maximun     |
|              | time (seconds) from the process being killed to recovered,   |
|              | is within the SLA                                            | 
|              |                                                              |
|              | Result: process_recover_time is within SLA limits, if not,   |
|              | test case failed and stopped                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 7        | Create a new VM in the existing neutron network              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 8        | start ip connectivity monitors from new VM:                  |
|              | 1. Check the L2 connectivity from the new VM to other VMs    |
|              |    in the neutron network.                                   |
|              | 2. Check the L3 connectivity from the new VM to VMs in       |
|              |    other neutron network.                                    |
|              | 3. Check the L3VPN SNAT connectivity from the new VM to      |
|              |    external network.                                         | 
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 9        | stop ip connectivity monitors after a period of time         |
|              | specified by “waiting_time”                                  |
|              |                                                              |
|              | Result: The monitor info will be aggregated                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 10       | verify the ip connectivity monitor resulta                   |
|              |                                                              |
|              | Result: ip connectivity monitor should not have any packet   |
|              | drop failures reported                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
