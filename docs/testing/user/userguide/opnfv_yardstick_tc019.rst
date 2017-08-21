.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC019
*************************************

+-----------------------------------------------------------------------------+
|Control Node Openstack Service High Availability                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC019_HA: Control node Openstack service down|
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of the      |
|              | service provided by OpenStack (like nova-api, neutro-server) |
|              | on control node.                                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case kills the processes of a specific Openstack   |
|              | service on a selected control node, then checks whether the  |
|              | request of the related Openstack command is OK and the       |
|              | killed processes are recovered.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "kill-process" is      |
|              | needed. This attacker includes three parameters:             |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "kill-process" in this   |
|              | test case.                                                   |
|              | 2) process_name: which is the process name of the specified  |
|              | OpenStack service. If there are multiple processes use the   |
|              | same name on the host, all of them are killed by this        |
|              | attacker.                                                    |
|              | 3) host: which is the name of a control node being attacked. |
|              |                                                              |
|              | e.g.                                                         |
|              | -fault_type: "kill-process"                                  |
|              | -process_name: "nova-api"                                    |
|              | -host: node1                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, two kinds of monitor are needed:          |
|              | 1. the "openstack-cmd" monitor constantly request a specific |
|              |    Openstack command, which needs two parameters:            |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scritps. It should be always set to              |
|              | "openstack-cmd" for this monitor.                            |
|              | 2) command_name: which is the command name used for request  |
|              |                                                              |
|              | 2. the "process" monitor check whether a process is running  |
|              |    on a specific node, which needs three parameters:         |
|              | 1) monitor_type: which used for finding the monitor class    |
|              | and related scritps. It should be always set to "process"    |
|              | for this monitor.                                            |
|              | 2) process_name: which is the process name for monitor       |
|              | 3) host: which is the name of the node runing the process    |
|              |                                                              |
|              | e.g.                                                         |
|              | monitor1:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "openstack server list"                       |
|              | monitor2:                                                    |
|              | -monitor_type: "process"                                     |
|              | -process_name: "nova-api"                                    |
|              | -host: node1                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are two metrics:                    |
|              | 1)service_outage_time: which indicates the maximum outage    |
|              | time (seconds) of the specified Openstack command request.   |
|              | 2)process_recover_time: which indicates the maximun time     |
|              | (seconds) from the process being killed to recovered         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Developed by the project. Please see folder:                 |
|              | "yardstick/benchmark/scenarios/availability/ha_tools"        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | ETSI NFV REL001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              | 1) test case file: opnfv_yardstick_tc019.yaml                |
|              | -Attackers: see above "attackers" discription                |
|              | -waiting_time: which is the time (seconds) from the process  |
|              | being killed to stoping monitors the monitors                |
|              | -Monitors: see above "monitors" discription                  |
|              | -SLA: see above "metrics" discription                        |
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
|step 3        | stop monitors after a period of time specified by            |
|              | "waiting_time"                                               |
|              |                                                              |
|              | Result: The monitor info will be aggregated.                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | verify the SLA                                               |
|              |                                                              |
|              | Result: The test case is passed or not.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|post-action   | It is the action when the test cases exist. It will check    |
|              | the status of the specified process on the host, and restart |
|              | the process if it is not running for next test cases         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
