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
|              | L3, SNAT Security Groups should continue to operate          |
|              | between the existing VMs while the SDN controller is         |
|              | offline or rebooting.                                        |
|              |                                                              |
|              | The test also validates that new network service operations  |
|              | (creating a new VM in the existing L2/L3 network or in a new |
|              | network...etc) are operational after the SDN controller      |
|              | has recovered from a failure.                                |
|              |                                                              |
|              | Finally, the test verifies that the SDN controller recovers  |
|              | within a given time bound to minimize the risk of a double   |
|              | failure in the system.                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case fails the SDN controller service running      |
|              | on the OpenStack controller node, then checks if already     |
|              | configured DHCP/ARP/L2/L3/SNAT connectivity is not           |
|              | impacted in the existing VMs and system is able to execute   |
|              | new virtual network operations once the opendaylight service |
|              | is restarted and fully recovered                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called “kill-process” is      |
|              | needed.This attacker includes three parameters:              |
|              |  1. fault_type: which is used for finding the attacker’s     |
|              |     scripts. It should be set to 'kill-process' in this test |
|              |                                                              |
|              |  2. process_name: should be set to sdn controller process    |
|              |                                                              |
|              |  3. host: which is the name of a control node where          |
|              |     opendaylight process is running                          |
|              |                                                              |
|              | e.g. -fault_type: “kill-process”                             |
|              |      -process_name: “opendaylight-karaf” (TBD)               |
|              |      -host: node1                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | This test case utilizes three monitors of type "ip-status"   |
|              | to track the following conditions:                           |
|              |  1. "ping_same_network_l2": monitor ping traffic between     |
|              |     the VMs in same neutron network                          |
|              |                                                              |
|              |  2. "ping_other_network_l3": monitor ping traffic between    |
|              |     the VMs in different neutron networks attached to same   |
|              |     neutron router                                           |
|              |                                                              |
|              |  3. "ping_external_snat": monitor ping traffic from VMs to   |
|              |     external destinations (e.g. google.com)                  |
|              |                                                              |
|              |  4. "SDN controller process monitor": a monitor checking the |
|              |     state of a specified SDN controller process. It measures |
|              |     the recovery time of the given process.                  |
|              |                                                              |
|              | Monitors of type "ip-status" use the "ping" utility to       |
|              | verify reachability of a given target IP.                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|operations    | In this test case, the following operations are needed:      |
|              |  1. "nova-create-instance-in_network": create a VM instance  |
|              |     in one of the existing neutron network.                  |
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
|references    | TBD                                                          |
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
|pre-action    |  1. The OpenStack Cluster is setup with SDN controller       |
|              |                                                              |
|              |  2. One or more neutron networks are created with two or     |
|              |     more VMs attached to each of the neutron networks.       |
|              |                                                              |
|              |  3. The neutron networks are attached to a neutron router    |
|              |     which is attached to an external network towards the     |
|              |     DCGW.                                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Start IP connectivity monitors:                              |
|              |  1. Check the L2 connectivity between the VMs in the same    |
|              |     neutron network.                                         |
|              |                                                              |
|              |  2. Check the L3 connectivity between VMs in different       |
|              |     neutron networks attached to neutron router.             |
|              |                                                              |
|              |  3. Check the SNAT connectivity from the VMs.                |
|              |     each monitor will run with independently process         |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Determine the VIM controller node on which sdn controller    |
|              | service is running                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Start attacker:                                              |
|              | SSH connect to the VIM node and kill sdn controller process  |
|              |                                                              |
|              | Result: the sdn controller service will be shutdown          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Verify the results of the IP connectivity monitors.          |
|              |                                                              |
|              | Result: The outage_time metric reported by the monitors      |
|              | is zero.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | Restart the SDN controller.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | Create a new VM in the existing neutron network              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 7        | Verify connectivity between VMs as follows:                  |
|              |  1. Check the L2 connectivity between VMs on the neutron     |
|              |     by sending a ICMP ping messages from the pre-existing to |
|              |     the new VM.                                              |
|              |                                                              |
|              |  2. Check the L3 connectivity from the pre-existing VM in a  |
|              |     a different Neutron network to the new VM.               |
|              |                                                              |
|              |  3. Check the SNAT connectivity from the new VM to           |
|              |     external network.                                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 8        | Stop IP connectivity monitors after a period of time         |
|              | specified by “waiting_time”                                  |
|              |                                                              |
|              | Result: The monitor info will be aggregated                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 9        | Verify the IP connectivity monitor results                   |
|              |                                                              |
|              | Result: IP connectivity monitor should not have any packet   |
|              | drop failures reported                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | This test Fails if the SLAs are not met, or if there is a    |
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

