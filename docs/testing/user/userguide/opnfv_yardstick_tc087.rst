.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson and others.

*************************************
Yardstick Test Case Description TC087
*************************************

+-----------------------------------------------------------------------------+
|SDN Controller resilience in non-HA configuration                            |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC087: SDN controller resilience in          |
|              | non-HA configuration                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test validates that network data plane services are     |
|              | highly available in the event of an SDN Controller failure,  |
|              | even if the SDN controller is deployed in a non-HA           |
|              | configuration. Specifically, the test verifies that          |
|              | existing data plane connectivity is not impacted, i.e. all   |
|              | configured network services such as DHCP, ARP, L2,           |
|              | L3 Security Groups should continue to operate                |
|              | between the existing VMs while the SDN controller is         |
|              | offline or rebooting.                                        |
|              |                                                              |
|              | The test also validates that new network service operations  |
|              | (creating a new VM in the existing L2/L3 network or in a new |
|              | network, etc.) are operational after the SDN controller      |
|              | has recovered from a failure.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case fails the SDN controller service running      |
|              | on the OpenStack controller node, then checks if already     |
|              | configured DHCP/ARP/L2/L3/SNAT connectivity is not           |
|              | impacted between VMs and the system is able to execute       |
|              | new virtual network operations once the SDN controller       |
|              | is restarted and has fully recovered                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called “kill-process” is      |
|              | needed. This attacker includes three parameters:             |
|              |  1. fault_type: which is used for finding the attacker's     |
|              |     scripts. It should be set to 'kill-process' in this test |
|              |                                                              |
|              |  2. process_name: should be set to the name of the SDN       |
|              |     controller process                                       |
|              |                                                              |
|              |  3. host: which is the name of a control node where the      |
|              |     SDN controller process is running                        |
|              |                                                              |
|              | e.g. -fault_type: "kill-process"                             |
|              |      -process_name: "opendaylight"                           |
|              |      -host: node1                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | This test case utilizes two monitors of type "ip-status"     |
|              | and one monitor of type "process" to track the following     |
|              | conditions:                                                  |
|              |  1. "ping_same_network_l2": monitor ICMP traffic between     |
|              |     VMs in the same Neutron network                          |
|              |                                                              |
|              |  2. "ping_external_snat": monitor ICMP traffic from VMs to   |
|              |     an external host on the Internet to verify SNAT          |
|              |     functionality.                                           |
|              |                                                              |
|              |  3. "SDN controller process monitor": a monitor checking the |
|              |     state of a specified SDN controller process. It measures |
|              |     the recovery time of the given process.                  |
|              |                                                              |
|              | Monitors of type "ip-status" use the "ping" utility to       |
|              | verify reachability of a given target IP.                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|operations    | In this test case, the following operations are needed:      |
|              |  1. "nova-create-instance-in_network": create a VM instance  |
|              |     in one of the existing Neutron network.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are two metrics:                    |
|              |  1. process_recover_time: which indicates the maximun        |
|              |     time (seconds) from the process being killed to          |
|              |     recovered                                                |
|              |                                                              |
|              |  2. packet_drop: measure the packets that have been dropped  |
|              |     by the monitors using pktgen.                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Developed by the project. Please see folder:                 |
|              | "yardstick/benchmark/scenarios/availability/ha_tools"        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | none                                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              |  1. test case file: opnfv_yardstick_tc087.yaml               |
|              |     - Attackers: see above “attackers” discription           |
|              |     - waiting_time: which is the time (seconds) from the     |
|              |       process being killed to stoping monitors the monitors  |
|              |     - Monitors: see above “monitors” discription             |
|              |     - SLA: see above “metrics” discription                   |
|              |                                                              |
|              |  2. POD file: pod.yaml The POD configuration should record   |
|              |     on pod.yaml first. the “host” item in this test case     |
|              |     will use the node name in the pod.yaml.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | Description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    |  1. The OpenStack cluster is set up with a single SDN        |
|              |     controller in a non-HA configuration.                    |
|              |                                                              |
|              |  2. One or more Neutron networks are created with two or     |
|              |     more VMs attached to each of the Neutron networks.       |
|              |                                                              |
|              |  3. The Neutron networks are attached to a Neutron router    |
|              |     which is attached to an external network towards the     |
|              |     DCGW.                                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Start IP connectivity monitors:                              |
|              |  1. Check the L2 connectivity between the VMs in the same    |
|              |     Neutron network.                                         |
|              |                                                              |
|              |  2. Check connectivity from one VM to an external host on    |
|              |     the Internet to verify SNAT functionality.
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Start attacker:                                              |
|              | SSH connect to the VIM node and kill the SDN controller      |
|              | process                                                      |
|              |                                                              |
|              | Result: the SDN controller service will be shutdown          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Verify the results of the IP connectivity monitors.          |
|              |                                                              |
|              | Result: The outage_time metric reported by the monitors      |
|              | is zero.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Restart the SDN controller.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | Create a new VM in the existing Neutron network              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | Verify connectivity between VMs as follows:                  |
|              |  1. Check the L2 connectivity between the previously         |
|              |     existing VM and the newly created VM on the same         |
|              |     Neutron network by sending ICMP messages                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 7        | Stop IP connectivity monitors after a period of time         |
|              | specified by “waiting_time”                                  |
|              |                                                              |
|              | Result: The monitor info will be aggregated                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 8        | Verify the IP connectivity monitor results                   |
|              |                                                              |
|              | Result: IP connectivity monitor should not have any packet   |
|              | drop failures reported                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | This test fails if the SLAs are not met or if there is a     |
|              | test case execution problem. The SLAs are define as follows  |
|              | for this test:                                               |
|              |  * SDN Controller recovery                                   |
|              |    * process_recover_time <= 30 sec                          |
|              |                                                              |
|              |  * no impact on data plane connectivity during SDN           |
|              |    controller failure and recovery.                          |
|              |    * packet_drop == 0                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+

