.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC086
*************************************

+-----------------------------------------------------------------------------+
|HA on VM the High Availability of hypervisor                                 |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC086: HA on VM-Verify the HA on Hypervisor  |
|              | Node                                                         |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of the      |
|              | Hypervisor Node. When the Hypervisor Node occur a panic      |//Hypervisor Node occur a panic
|              | failure, this test case will observe whether the VM1 can be  |
|              | automatically rebuilt on other active nodes.                 |
+--------------+--------------------------------------------------------------+
|test method   | This test case will log in Hypervisor Node and construct the |
|              | panic failure, and observe whether the VM1 can be            |
|              | automatically rebuilt on other active nodes, observe whether |
|              | the failed VM is successfully fenced, observe the recovery   |
|              | of L2,L3,L3VPN traffic to that new VM IP address.            |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "node-pause" is needed.|
|              | This attacker includes two parameters:                       |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "node-pause" in this     |
|              | test case.                                                   |
|              | 2) host: the name of a compute node being attacked.          |//compute node
|              |                                                              |
|              | e.g.                                                         |
|              | -fault_type: "node-pause"                                    |
|              | -host: node1                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, the following monitors are needed:        |
|              | 1. The "node-status" monitor will check whether the status   |
|              | of Hypervisor Node will become pause. This monitor has the   |
|              | following parameters:                                        |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scritps. It should be always set to "node-status"|
|              | for this monitor;                                            |
|              |                                                              |
|              | 2. The "vm1-status" monitor will check whether the status of |
|              | VM1 will shut down and then automatically rebuilt on other   |
|              | active nodes. This monitor has the following parameters:     |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scritps. It should be always set to "vm1-status" |
|              | for this monitor;                                            |
|              |                                                              |
|              | (e.g.)                                                       |
|              | monitor1:                                                    |
|              | -monitor_type: "node-status"                                 |
|              | monitor2:                                                    |
|              | -monitor_type: "vm1-status"                                  |
+--------------+--------------------------------------------------------------+
|checkers      | In this test case, a checker called "node-health" is needed: |
|              | 1. The "node-health" checker that checks whether a Hypervisor|
|              | Node is normally running. This checker has the following     |
|              | parameters:                                                  |
|              | 1) checker_type: which is used for finding the result        |
|              | checker class and related scripts. In this case the checker  |
|              | type will be "node-health";                                  |
|              | 2) host_ip: the ip address of the target Hypervisor Node.    |
|              |                                                              |
|              | (e.g.)                                                       |
|              | checker1:                                                    |
|              | -checker_type: "node-health"                                 |
|              | -host_ip: 172.16.1.11                                        |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there is two metrics:                     |
|              | 1)node_status: which indicates the Hypervisor Node is shut   |
|              | down.                                                        |
|              | 1)vm1_status: which indicates the VM1 is automatically       |
|              | rebuild on other active nodes.                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Developed by the project. Please see folder:                 |
|              | "yardstick/benchmark/scenarios/availability/ha_tools"        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              | 1) test case file:                                           |
|              | -Attackers: see above "attackers" description                |
|              | -waiting_time: which is the time (seconds) from the process  |
|              | being killed to stoping monitors the monitors                |
|              | -Monitors: see above "monitors" description                  |
|              | -SLA: see above "metrics" description                        |
|              |                                                              |
|              | 2)POD file: pod.yaml                                         |
|              | The POD configuration should record on pod.yaml first.       |
|              | the "host" item in this test case will use the node name in  |
|              | the pod.yaml.                                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    | It is the action before the test case starts, 1)The system   |
|              | is running normally. 2)VIM has been deployed. 3)Project is   |
|              | admin and the VM1 can be rebuild offsite or support HA       |
+--------------+--------------------------------------------------------------+
|step 1        | Determine the one Hypervisor Node through the IP addr which  |//Hypervisor Node
|              | is provided by OpenStack                                     |
|              |                                                              |
|              | Result: The IP of the Hypervisor Node is got.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | do attacker: Remote log in the Hypervisor Node to check the  |
|              | VM1’s condition and construct the panic failure on this      |
|              | node using the command:                                      |
|              | echo 1 > /proc/sys/kernel/sysrq                              |
|              | echo c > /proc/sysrq-trigger                                 |
|              |                                                              |
|              | Result: The VM will be paused.                               |//这个状态有待讨论，不是pause
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | do monitor: Observe whether the VM1 can be automatically     |
|              | rebuilt on other active nodes. Observe whether the failed VM |
|              | is successfully fenced. Observe the recovery of L2,L3,L3VPN  |
|              | traffic to that new VM IP address.                           |
|              |                                                              |
|              | Result: The VM1 can be automatically rebuilt on other active |
|              | nodes. The failed VM is successfully fenced. The recovery of |
|              | L2,L3,L3VPN traffic to that new VM IP address.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | do checker: When the Hypervisor Node is down, VM1 can be     |
|              | automatically rebuilt on other active nodes.                 |
|              |                                                              |
|              | Result: The VM1 can be automatically rebuilt on other active |
|              | nodes.                                                       |
+--------------+--------------------------------------------------------------+
|post-action   | It is the action when the test cases exist. It will check    |
|              | the status of the specified process on the host, and restart |
|              | the process if it is not running for next test cases.        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+