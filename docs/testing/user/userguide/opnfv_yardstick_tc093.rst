.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intracom Telecom and others.
.. mardim@intracom-telecom.com

*************************************
Yardstick Test Case Description TC093
*************************************

+-----------------------------------------------------------------------------+
|SDN Vswitch resilience in non-HA or HA configuration                         |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC093: SDN Vswitch resilience in             |
|              | non-HA or HA configuration                                   |
+--------------+--------------------------------------------------------------+
|test purpose  | This test validates that network data plane services are     |
|              | resilient in the event of Virtual Switch failure             |
|              | in compute nodes. Specifically, the test verifies that       |
|              | existing data plane connectivity is not permanently impacted |
|              | i.e. all configured network services such as DHCP, ARP, L2,  |
|              | L3 Security Groups continue to operate between the existing  |
|              | VMs eventually after the Virtual Switches have finished      |
|              | rebooting.                                                   |
|              |                                                              |
|              | The test also validates that new network service operations  |
|              | (creating a new VM in the existing L2/L3 network or in a new |
|              | network, etc.) are operational after the Virtual Switches    |
|              | have recovered from a failure.                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This testcase first checks if the already configured         |
|              | DHCP/ARP/L2/L3/SNAT connectivity is proper. After            |
|              | it fails and restarts again the VSwitch services which are   |
|              | running on both OpenStack compute nodes, and then checks if  |
|              | already configured DHCP/ARP/L2/L3/SNAT connectivity is not   |
|              | permanently impacted (even if there are some packet          |
|              | loss events) between VMs and the system is able to execute   |
|              | new virtual network operations once the Vswitch services     |
|              | are restarted and have been fully recovered                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, two attackers called “kill-process” are   |
|              | needed. These attackers include three parameters:            |
|              |                                                              |
|              | 1. fault_type: which is used for finding the attacker's      |
|              |    scripts. It should be set to 'kill-process' in this test  |
|              |                                                              |
|              | 2. process_name: should be set to the name of the Vswitch    |
|              |    process                                                   |
|              |                                                              |
|              | 3. host: which is the name of the compute node where the     |
|              |    Vswitch process is running                                |
|              |                                                              |
|              | e.g. -fault_type: "kill-process"                             |
|              |      -process_name: "openvswitch"                            |
|              |      -host: node1                                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | This test case utilizes two monitors of type "ip-status"     |
|              | and one monitor of type "process" to track the following     |
|              | conditions:                                                  |
|              |                                                              |
|              | 1. "ping_same_network_l2": monitor ICMP traffic between      |
|              |    VMs in the same Neutron network                           |
|              |                                                              |
|              | 2. "ping_external_snat": monitor ICMP traffic from VMs to    |
|              |    an external host on the Internet to verify SNAT           |
|              |    functionality.                                            |
|              |                                                              |
|              | 3. "Vswitch process monitor": a monitor checking the         |
|              |    state of the specified Vswitch process. It measures       |
|              |    the recovery time of the given process.                   |
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
|              |  2. outage_time: measures the total time in which            |
|              |     monitors were failing in their tasks (e.g. total time of |
|              |     Ping failure)                                            |
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
|              |  1. test case file: opnfv_yardstick_tc093.yaml               |
|              |                                                              |
|              |     - Attackers: see above “attackers” description           |
|              |     - monitor_time: which is the time (seconds) from         |
|              |       starting to stoping the monitors                       |
|              |     - Monitors: see above “monitors” discription             |
|              |     - SLA: see above “metrics” description                   |
|              |                                                              |
|              |  2. POD file: pod.yaml The POD configuration should record   |
|              |     on pod.yaml first. the “host” item in this test case     |
|              |     will use the node name in the pod.yaml.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | Description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    |  1. The Vswitches are set up in both compute nodes.          |
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
|              |     the Internet to verify SNAT functionality.               |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Start attackers:                                             |
|              | SSH connect to the VIM compute nodes and kill the Vswitch    |
|              | processes                                                    |
|              |                                                              |
|              | Result: the SDN Vswitch services will be shutdown            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Verify the results of the IP connectivity monitors.          |
|              |                                                              |
|              | Result: The outage_time metric reported by the monitors      |
|              | is not greater than the max_outage_time.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Restart the SDN Vswitch services.                            |
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
|              | specified by “monitor_time”                                  |
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
|              | * SDN Vswitch recovery                                       |
|              |                                                              |
|              |   * process_recover_time <= 30 sec                           |
|              |                                                              |
|              | * no impact on data plane connectivity during SDN            |
|              |   Vswitch failure and recovery.                              |
|              |                                                              |
|              |   * packet_drop == 0                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+

