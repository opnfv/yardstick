.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC086
*************************************

+-----------------------------------------------------------------------------+
|VM High Availability when Hypervisor Node Failure Occurs                     |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC086: Verify VM HA on Hypervisor Node       |
|              | Failure                                                      |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of the VM   |
|              | when hypervisor failure happens. When the Hypervisor Node    |
|              | occurs a panic failure, this test case will observe whether  |
|              | the VM can be automatically rebuilt on other active nodes.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case will log in Hypervisor Node and construct the |
|              | panic failure, observe whether the VM can be                 |
|              | automatically rebuilt on other active nodes, observe whether |
|              | the failed VM is successfully fenced, and observe the        |
|              | recovery of L2, L3 and L3VPN traffic to that new VM IP       |
|              | address.                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "node-panic" is needed.|
|              | This attacker is user to construct panic failure on a        |
|              | specific compute node.                                       |
|              | This attacker includes two parameters:                       |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "node-panic" in this     |
|              | test case.                                                   |
|              | 2) host: the name of a compute node being attacked.          |
|              |                                                              |
|              | e.g.                                                         |
|              |  - fault_type: "node-panic"                                  |
|              |  - host: node1                                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, the following monitors are needed:        |
|              | 1. The "node-status" monitor will check whether the status   |
|              | of Hypervisor Node will become down. This monitor has the    |
|              | following parameters:                                        |
|              |  - monitor_type: which is used for finding the monitor class |
|              |    and related scripts. It should be always set to           |
|              |    "node-status" for this monitor;                           |
|              |                                                              |
|              | 2. The "vm1-info" monitor will monitor the info of VM1 to    |
|              | check whether the VM1 can be automatically rebuilt on other  |
|              | active nodes, such as VM1 id, VM1 IP address, Hypervisor Node|
|              | id on which VM1 is rebuilt. This monitor has the following   |
|              | parameters:                                                  |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scripts. It should be always set to "vm1-info"   |
|              | for this monitor;                                            |
|              |                                                              |
|              |                                                              |
|              | 3. The "vm-status" monitor will check whether the status of  |
|              | VM will shut down and failed VM is successfully fenced. This |
|              | monitor has the following parameters:                        |
|              |  - monitor_type: which is used for finding the monitor class |
|              |    and related scripts. It should be always set to           |
|              |    "vm-status" for this monitor;                             |
|              |                                                              |
|              | 4. The "vm1-connectivity" monitor will observe the recovery  |
|              | of L2,L3,L3VPN traffic to the IP address of the new VM. This |
|              | monitor has the following parameters:                        |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scritps. It should be always set to              |
|              | "vm1-connectivity" for this monitor;                         |
|              |                                                              |
|              | (e.g.)                                                       |
|              | monitor1:                                                    |
|              | -monitor_type: "node-status"                                 |
|              | monitor2:                                                    |
|              | -monitor_type: "vm1-info"                                    |
|              | monitor3:                                                    |
|              | -monitor_type: "vm1-status"                                  |
|              | monitor4:                                                    |
|              | -monitor_type: "vm1-connectivity"                            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|checkers      | In this test case, a checker called "node-health" is needed: |
|              | The "node-health" checker that checks whether a Hypervisor   |
|              | Node is up and one can ssh on it. This checker has the       |
|              | following parameters:                                        |  
|              |                                                              |
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
|metrics       | In this test case, there are two metrics:                    |
|              | 1)node_status: which indicates the Hypervisor Node is shut   |
|              | down.                                                        |
|              | 2)vm_status: which indicates the VM is automatically         |
|              | rebuild on other active nodes.                               |
|              | 3)vm1_connectivity - which determines whether L2/L3/L3VPN    |
|              | traffic thru the VM is recovered [ and possibly how much     |
|              | packet loss occurred ]                                       |
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
|              | -checker: see above "checker" description                    |
|              | -SLA: see above "metrics" description                        |
|              |                                                              |
|              | 2)POD file: pod.yaml                                         |
|              | The pod.yaml file contains host and login information about  |
|              | the nodes in the POD. The "nodes" mentioned in this test case|
|              | description need to be defined in the pod.yaml               | 
|              | correspondingly.                                             |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    | It is the action before the test case starts, 1)The system   |
|              | is running normally. 2)VIM has been deployed. 3)Project is   |
|              | admin and the VM1 can be rebuild offsite or support HA       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Determine the one Hypervisor Node through the IP addr which  |
|              | is provided by OpenStack                                     |
|              |                                                              |
|              | Result: The IP of the Hypervisor Node is got.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | do attacker: Remote log in the Hypervisor Node to check the  |
|              | VM1's condition and construct the panic failure on this      |
|              | node using the command:                                      |
|              | echo 1 > /proc/sys/kernel/sysrq                              |
|              | echo c > /proc/sysrq-trigger                                 |
|              |                                                              |
|              | Result: The Hypervisor Node is halted due to panic, and      |
|              | because of the halted Hypervisor Node, the VM will no        |
|              | longer be running.                                           |
|              |                                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | do monitor: Observe the status of Hypervisor Node. Check     |
|              | whether the Hypervisor Node is down.                         |
|              |                                                              |
|              | Result: The Hypervisor Node is down.                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | do monitor: The rebuilted VM is indicated as VM2. Observe the|              
|              | id and IP address of the VM2, and observe Hypervisor Node id |
|              | which VM2 rebuilt. Check whether the VM2 can be automatically|
|              |rebuilt on other active nodes.                                |
|              |                                                              |
|              | Result: The VM2 can be automatically rebuilt on other active |
|              | nodes.                                                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | do monitor: Observe whether the status of VM1 become down and|
|              | is successfully fenced                                       |
|              |                                                              |
|              | Result: The failed VM is successfully fenced.                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | do monitor: Remote log in the controller node, ping the new  |
|              |VM (with the same IP)                                         |
|              |                                                              |
|              | Result: The recovery of L2,L3,L3VPN traffic to that new VM   |
|              | IP address.                                                  |
|              |                                                              |
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
