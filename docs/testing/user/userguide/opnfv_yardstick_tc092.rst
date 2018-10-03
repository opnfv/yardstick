.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson and others.

*************************************
Yardstick Test Case Description TC092
*************************************

+-----------------------------------------------------------------------------+
|SDN Controller resilience in HA configuration                                |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC092: SDN controller resilience and high    |
|              | availability HA configuration                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test validates SDN controller node high availability by |
|              | verifying there is no impact on the data plane connectivity  |
|              | when one SDN controller fails in a HA configuration,         |
|              | i.e. all existing configured network services DHCP, ARP, L2, |
|              | L3VPN, Security Groups should continue to operate            |
|              | between the existing VMs while one SDN controller instance   |
|              | is offline and rebooting.                                    |
|              |                                                              |
|              | The test also validates that network service operations such |
|              | as creating a new VM in an existing or new L2 network        |
|              | network remain operational while one instance of the         |
|              | SDN controller is offline and recovers from the failure.     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case:                                              |
|              |  1. fails one instance of a SDN controller cluster running   |
|              |     in a HA configuration on the OpenStack controller node   |
|              |                                                              |
|              |  2. checks if already configured L2 connectivity between     |
|              |     existing VMs is not impacted                             |
|              |                                                              |
|              |  3. verifies that the system never loses the ability to      |
|              |     execute virtual network operations, even when the        |
|              |     failed SDN Controller is still recovering                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called “kill-process” is      |
|              | needed. This attacker includes three parameters:             |
|              |                                                              |
|              |  1. ``fault_type``: which is used for finding the attacker's |
|              |     scripts. It should be set to 'kill-process' in this test |
|              |                                                              |
|              |  2. ``process_name``: should be set to sdn controller        |
|              |     process                                                  |
|              |                                                              |
|              |  3. ``host``: which is the name of a control node where      |
|              |     opendaylight process is running                          |
|              |                                                              |
|              | example:                                                     |
|              |   - ``fault_type``: “kill-process”                           |
|              |   - ``process_name``: “opendaylight-karaf” (TBD)             |
|              |   - ``host``: node1                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, the following monitors are needed         |
|              |  1. ``ping_same_network_l2``: monitor pinging traffic        |
|              |     between the VMs in same neutron network                  |
|              |                                                              |
|              |  2. ``ping_external_snat``: monitor ping traffic from VMs to |
|              |     external destinations (e.g. google.com)                  |
|              |                                                              |
|              |  3. ``SDN controller process monitor``: a monitor checking   |
|              |     the state of a specified SDN controller process. It      |
|              |     measures the recovery time of the given process.         |
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
|              | 1. test case file: opnfv_yardstick_tc092.yaml                |
|              |                                                              |
|              |    - Attackers: see above “attackers” discription            |
|              |    - Monitors: see above “monitors” discription              |
|              |                                                              |
|              |      - waiting_time: which is the time (seconds) from the    |
|              |        process being killed to stoping monitors the          |
|              |        monitors                                              |
|              |                                                              |
|              |    - SLA: see above “metrics” discription                    |
|              |                                                              |
|              | 2. POD file: pod.yaml The POD configuration should record    |
|              |    on pod.yaml first. the “host” item in this test case      |
|              |    will use the node name in the pod.yaml.                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | Description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    |  1. The OpenStack cluster is set up with an SDN controller   |
|              |     running in a three node cluster configuration.           |
|              |                                                              |
|              |  2. One or more neutron networks are created with two or     |
|              |     more VMs attached to each of the neutron networks.       |
|              |                                                              |
|              |  3. The neutron networks are attached to a neutron router    |
|              |     which is attached to an external network the towards     |
|              |     DCGW.                                                    |
|              |                                                              |
|              |  4. The master node of SDN controller cluster is known.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Start ip connectivity monitors:                              |
|              |  1. Check the L2 connectivity between the VMs in the same    |
|              |     neutron network.                                         |
|              |                                                              |
|              |  2. Check the external connectivity of the VMs.              |
|              |                                                              |
|              | Each monitor runs in an independent process.                 |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Start attacker:                                              |
|              | SSH to the VIM node and kill the SDN controller process      |
|              | determined in step 2.                                        |
|              |                                                              |
|              | Result: One SDN controller service will be shut down         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | Restart the SDN controller.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | Create a new VM in the existing Neutron network while the    |
|              | SDN controller is offline or still recovering.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | Stop IP connectivity monitors after a period of time         |
|              | specified by “waiting_time”                                  |
|              |                                                              |
|              | Result: The monitor info will be aggregated                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | Verify the IP connectivity monitor result                    |
|              |                                                              |
|              | Result: IP connectivity monitor should not have any packet   |
|              | drop failures reported                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 7        | Verify process_recover_time, which indicates the maximun     |
|              | time (seconds) from the process being killed to recovered,   |
|              | is within the SLA. This step blocks until either the         |
|              | process has recovered or a timeout occurred.                 |
|              |                                                              |
|              | Result: process_recover_time is within SLA limits, if not,   |
|              | test case failed and stopped.                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 8        | Start IP connectivity monitors for the  new VM:              |
|              |                                                              |
|              | 1. Check the L2 connectivity from the existing VMs to the    |
|              |    new VM in the Neutron network.                            |
|              |                                                              |
|              | 2. Check connectivity from one VM to an external host on     |
|              |    the Internet to verify SNAT functionality.                |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 9        | Stop IP connectivity monitors after a period of time         |
|              | specified by “waiting_time”                                  |
|              |                                                              |
|              | Result: The monitor info will be aggregated                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 10       | Verify the IP connectivity monitor result                    |
|              |                                                              |
|              | Result: IP connectivity monitor should not have any packet   |
|              | drop failures reported                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+

