.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Yin Kanglin and others.
.. 14_ykl@tongji.edu.cn

*************************************
Yardstick Test Case Description TC052
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Controller Node Disk I/O Block High Availability                   |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC052: OpenStack Controller Node Disk I/O    |
|              | Block High Availability                                      |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of control  |
|              | node. When the disk I/O of a specified disk is blocked,      |
|              | which breaks down the Openstack services on this node. Read  |
|              | and write services should still be accessed by other         |
|              | controller nodes, and the services on failed controller node |
|              | should be isolated.                                          |
+--------------+--------------------------------------------------------------+
|test method   | This test case blocks the disk I/O of a specified control    |
|              | node, then checks whether the services that need to read or  |
|              | wirte the disk of the control node are OK with some monitor  |
|              | tools.                                                       |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "disk-block" is        |
|              | needed. This attacker includes two parameters:               |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "disk-block" in this     |
|              | test case.                                                   |
|              | 2) host: which is the name of a control node being attacked. |
|              | e.g.                                                         |
|              | -fault_type: "disk-block"                                    |
|              | -host: node1                                                 |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, two kinds of monitor are needed:          |
|              | 1. the "openstack-cmd" monitor constantly request a specific |
|              | Openstack command, which needs two parameters:               |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scripts. It should be always set to              |
|              | "openstack-cmd" for this monitor.                            |
|              | 2) command_name: which is the command name used for request. |
|              |                                                              |
|              | e.g.                                                         |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "nova flavor-list"                            |
|              |                                                              |
|              | 2. the second monitor verifies the read and write function   |
|              | by a "operation" and a "result checker".                     |
|              | the "operation" have two parameters:                         |
|              | 1) operation_type: which is used for finding the operation   |
|              | class and related scripts.                                   |
|              | 2) action_parameter: parameters for the operation.           |
|              | the "result checker" have three parameters:                  |
|              | 1) checker_type: which is used for finding the reuslt        |
|              | checker class and realted scripts.                           |
|              | 2) expectedValue: the expected value for the output of the   |
|              | checker script.                                              |
|              | 3) condition: whether the expected value is in the output of |
|              | checker script or is totally same with the output.           |
|              |                                                              |
|              | In this case, the "operation" adds a flavor and the "result  |
|              | checker" checks whether ths flavor is created. Their         |
|              | parameters show as follows:                                  |
|              | operation:                                                   |
|              | -operation_type: "nova-create-flavor"                        |
|              | -action_parameter:                                           |
|              |    flavorconfig: "test-001 test-001 100 1 1"                 |
|              | result checker:                                              |
|              | -checker_type: "check-flavor"                                |
|              | -expectedValue: "test-001"                                   |
|              | -condition: "in"                                             |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there is one metric:                      |
|              | 1)service_outage_time: which indicates the maximum outage    |
|              | time (seconds) of the specified Openstack command request.   |
+--------------+--------------------------------------------------------------+
|test tool     | Developed by the project. Please see folder:                 |
|              | "yardstick/benchmark/scenarios/availability/ha_tools"        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | ETSI NFV REL001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              | 1) test case file: opnfv_yardstick_tc052.yaml                |
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
|step 1        | do attacker: connect the host through SSH, and then execute  |
|              | the block disk I/O script on the host.                       |
|              |                                                              |
|              | Result: The disk I/O of the host will be blocked             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | start monitors:                                              |
|              | each monitor will run with independently process             |
|              |                                                              |
|              | Result: The monitor info will be collected.                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | do operation: add a flavor                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | do result checker: check whether the falvor is created       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 5        | stop monitors after a period of time specified by            |
|              | "waiting_time"                                               |
|              |                                                              |
|              | Result: The monitor info will be aggregated.                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 6        | verify the SLA                                               |
|              |                                                              |
|              | Result: The test case is passed or not.                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|post-action   | It is the action when the test cases exist. It excutes the   |
|              | release disk I/O script to release the blocked I/O.          |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails if monnitor SLA is not passed or the result checker is |
|              | not passed, or if there is a test case execution problem.    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
