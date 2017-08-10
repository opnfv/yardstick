.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Yin Kanglin and others.
.. 14_ykl@tongji.edu.cn

*************************************
Yardstick Test Case Description TC058
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Controller Virtual Router Service High Availability                |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC058:OpenStack Controller Virtual Router    |
|              | Service High Availability                                    |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of virtual  |
|              | routers(L3 agent) on controller node. When a virtual router  |
|              | service on a specified controller node is shut down, this    |
|              | test case will check whether the network of virtual machines |
|              | will be affected, and whether the attacked virtual router    |
|              | service will be recovered.                                   |
+--------------+--------------------------------------------------------------+
|test method   | This test case kills the processes of virtual router service |
|              | (l3-agent) on a selected controller node(the node holds the  |
|              | active l3-agent), then checks whether the network routing    |
|              | of virtual machines is OK and whether the killed service     |
|              | will be recovered.                                           |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "kill-process" is      |
|              | needed. This attacker includes three parameters:             |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "kill-process" in this   |
|              | test case.                                                   |
|              | 2) process_name: which is the process name of the load       |
|              | balance service. If there are multiple processes use the     |
|              | same name on the host, all of them are killed by this        |
|              | attacker.                                                    |
|              | 3) host: which is the name of a control node being attacked. |
|              |                                                              |
|              | In this case, this process name should set to "l3agent" ,    |
|              | for example                                                  |
|              | -fault_type: "kill-process"                                  |
|              | -process_name: "l3agent"                                     |
|              | -host: node1                                                 |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, two kinds of monitor are needed:          |
|              | 1. the "ip_status" monitor that pings a specific ip to check |
|              | the connectivity of this ip, which needs two parameters:     |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scripts. It should be always set to "ip_status"  |
|              | for this monitor.                                            |
|              | 2) ip_address: The ip to be pinged. In this case, ip_address |
|              | will be either an ip address of external network or an ip    |
|              | address of a virtual machine.                                |
|              | 3) host: The node on which ping will be executed, in this    |
|              | case the host will be a virtual machine.                     |
|              |                                                              |
|              | 2. the "process" monitor check whether a process is running  |
|              | on a specific node, which needs three parameters:            |
|              | 1) monitor_type: which used for finding the monitor class    |
|              | and related scripts. It should be always set to "process"    |
|              | for this monitor.                                            |
|              | 2) process_name: which is the process name for monitor. In   |
|              | this case, the process-name of monitor2 should be "l3agent"  |
|              | 3) host: which is the name of the node running the process   |
|              |                                                              |
|              | e.g.                                                         |
|              | monitor1-1:                                                  |
|              | -monitor_type: "ip_status"                                   |
|              | -host: 172.16.0.11                                           |
|              | -ip_address: 172.16.1.11                                     |
|              | monitor1-2:                                                  |
|              | -monitor_type: "ip_status"                                   |
|              | -host: 172.16.0.11                                           |
|              | -ip_address: 8.8.8.8                                         |
|              | monitor2:                                                    |
|              | -monitor_type: "process"                                     |
|              | -process_name: "l3agent"                                     |
|              | -host: node1                                                 |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are two metrics:                    |
|              | 1)service_outage_time: which indicates the maximum outage    |
|              | time (seconds) of the specified Openstack command request.   |
|              | 2)process_recover_time: which indicates the maximum time     |
|              | (seconds) from the process being killed to recovered         |
+--------------+--------------------------------------------------------------+
|test tool     | None. Self-developed.                                        |
+--------------+--------------------------------------------------------------+
|references    | ETSI NFV REL001                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              | 1) test case file: opnfv_yardstick_tc058.yaml                |
|              | -Attackers: see above "attackers" description                |
|              | -Monitors: see above "monitors" description                  |
|              | -Steps: the test case execution step, see "test sequence"    |
|              | description below                                            |
|              |                                                              |
|              | 2)POD file: pod.yaml                                         |
|              | The POD configuration should record on pod.yaml first.       |
|              | the "host" item in this test case will use the node name in  |
|              | the pod.yaml.                                                |
+--------------+------+----------------------------------+--------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with cachestat included in the image.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | Two host VMs are booted, these two hosts are in two different|
|              | networks, the networks are connected by a virtual router     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | start monitors:                                              |
|              | each monitor will run with independently process             |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | do attacker: connect the host through SSH, and then execute  |
|              | the kill process script with param value specified by        |
|              | "process_name"                                               |
|              |                                                              |
|              | Result: Process will be killed.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | stop monitors after a period of time specified by            |
|              | "waiting_time"                                               |
|              |                                                              |
|              | Result: The monitor info will be aggregated.                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | verify the SLA                                               |
|              |                                                              |
|              | Result: The test case is passed or not.                      |
|              |                                                              |
+--------------+------+----------------------------------+--------------------+
|post-action   | It is the action when the test cases exist. It will check    |
|              | the status of the specified process on the host, and restart |
|              | the process if it is not running for next test cases.        |
|              | Virtual machines and network created in the test case will   |
|              | be destoryed.                                                |
|              |                                                              |
+--------------+------+----------------------------------+--------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
+--------------+--------------------------------------------------------------+
