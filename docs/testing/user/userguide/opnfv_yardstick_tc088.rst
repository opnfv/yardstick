.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Yin Kanglin and others.
.. 14_ykl@tongji.edu.cn

*************************************
Yardstick Test Case Description TC088
*************************************

+-----------------------------------------------------------------------------+
|Control Node Openstack Service High Availability - Nova Scheduler            |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC088: Control node Openstack service down - |
|              | nova scheduler                                               |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of the      |
|              | compute scheduler service provided by OpenStack (nova-       |
|              | scheduler) on control node.                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test method   | This test case kills the processes of nova-scheduler service |
|              | on a selected control node, then checks whether the request  |
|              | of the related OpenStack command is OK and the killed        |
|              | processes are recovered.                                     |
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
|              | In this case. This parameter should always set to "nova-     |
|              | scheduler".                                                  |
|              | 3) host: which is the name of a control node being attacked. |
|              |                                                              |
|              | e.g.                                                         |
|              | -fault_type: "kill-process"                                  |
|              | -process_name: "nova-scheduler"                              |
|              | -host: node1                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, one kind of monitor is needed:            |
|              | 1. the "process" monitor check whether a process is running  |
|              | on a specific node, which needs three parameters:            |
|              | 1) monitor_type: which used for finding the monitor class and|
|              | related scripts. It should be always set to "process"        |
|              | for this monitor.                                            |
|              | 2) process_name: which is the process name for monitor       |
|              | 3) host: which is the name of the node running the process   |
|              |                                                              |
|              | e.g.                                                         |
|              | monitor:                                                     |
|              | -monitor_type: "process"                                     |
|              | -process_name: "nova-scheduler"                              |
|              | -host: node1                                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|operations    | In this test case, the following operations are needed:      |
|              | 1. "nova-create-instance": create a VM instance to check     |
|              | whether the nova-scheduler works normally.                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are one metric:                     |
|              | 1)process_recover_time: which indicates the maximum time     |
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
|              | 1) test case file: opnfv_yardstick_tc088.yaml                |
|              | -Attackers: see above "attackers" description                |
|              | -waiting_time: which is the time (seconds) from the process  |
|              | being killed to stopping monitors the monitors               |
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
|step 1        | do attacker: connect the host through SSH, and then execute  |
|              | the kill process script with param value specified by        |
|              | "process_name"                                               |
|              |                                                              |
|              | Result: Process will be killed.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | start monitors:                                              |
|              | each monitor will run with independently process             |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | create a new instance to check whether the nova scheduler    |
|              | works normally.                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | stop the monitor after a period of time specified by         |
|              | "waiting_time"                                               |
|              |                                                              |
|              | Result: The monitor info will be aggregated.                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|post-action   | It is the action when the test cases exist. It will check the|
|              | status of the specified process on the host, and restart the |
|              | process if it is not running for next test cases             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
