.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Yin Kanglin and others.
.. 14_ykl@tongji.edu.cn

*************************************
Yardstick Test Case Description TC057
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Controller Cluster Management Service High Availability            |
+==============+==============================================================+
|test case id  |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the quorum configuration of the   |
|              | cluster manager(pacemaker) on controller nodes. When a       |
|              | controller node , which holds all active application         |
|              | resources, failed to communicate with other cluster nodes    |
|              | (via corosync), the test case will check whether the standby |
|              | application resources will take place of those active        |
|              | application resources which should be regarded to be down in |
|              | the cluster manager.                                         |
+--------------+--------------------------------------------------------------+
|test method   | This test case kills the processes of cluster messaging      |
|              | service(corosync) on a selected controller node(the node     |
|              | holds the active application resources), then checks whether |
|              | active application resources are switched to other           |
|              | controller nodes and whether the Openstack commands are OK.  |
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
|              | In this case, this process name should set to "corosync" ,   |
|              | for example                                                  |
|              | -fault_type: "kill-process"                                  |
|              | -process_name: "corosync"                                    |
|              | -host: node1                                                 |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, a kind of monitor is needed:              |
|              | 1. the "openstack-cmd" monitor constantly request a specific |
|              |    Openstack command, which needs two parameters:            |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scripts. It should be always set to              |
|              | "openstack-cmd" for this monitor.                            |
|              | 2) command_name: which is the command name used for request  |
|              |                                                              |
|              | In this case, the command_name of monitor1 should be services|
|              | that are managed by the cluster manager. (Since rabbitmq and |
|              | haproxy are managed by pacemaker, most Openstack Services    |
|              | can be used to check high availability in this case)         |
|              |                                                              |
|              | (e.g.)                                                       |
|              | monitor1:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "nova image-list"                             |
|              | monitor2:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "neutron router-list"                         |
|              | monitor3:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "heat stack-list"                             |
|              | monitor4:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "cinder list"                                 |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|checkers      | In this test case, a checker is needed, the checker will     |
|              | the status of application resources in pacemaker and the     |
|              | checker have three parameters:                               |
|              | 1) checker_type: which is used for finding the result        |
|              | checker class and related scripts. In this case the checker  |
|              | type will be "pacemaker-check-resource"                      |
|              | 2) resource_name: the application resource name              |
|              | 3) resource_status: the expected status of the resource      |
|              | 4) expectedValue: the expected value for the output of the   |
|              | checker script, in the case the expected value will be the   |
|              | identifier in the cluster manager                            |
|              | 3) condition: whether the expected value is in the output of |
|              | checker script or is totally same with the output.           |
|              | (note: pcs is required to installed on controller node in    |
|              | order to run this checker)                                   |
|              |                                                              |
|              | (e.g.)                                                       |
|              | checker1:                                                    |
|              | -checker_type: "pacemaker-check-resource"                    |
|              | -resource_name: "p_rabbitmq-server"                          |
|              | -resource_status: "Stopped"                                  |
|              | -expectedValue: "node-1"                                     |
|              | -condition: "in"                                             |
|              | checker2:                                                    |
|              | -checker_type: "pacemaker-check-resource"                    |
|              | -resource_name: "p_rabbitmq-server"                          |
|              | -resource_status: "Master"                                   |
|              | -expectedValue: "node-2"                                     |
|              | -condition: "in"                                             |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are two metrics:                    |
|              | 1)service_outage_time: which indicates the maximum outage    |
|              | time (seconds) of the specified Openstack command request.   |
+--------------+--------------------------------------------------------------+
|test tool     | None. Self-developed.                                        |
+--------------+--------------------------------------------------------------+
|references    | ETSI NFV REL001                                              |
+--------------+--------------------------------------------------------------+
|configuration | This test case needs two configuration files:                |
|              | 1) test case file: opnfv_yardstick_tc057.yaml                |
|              | -Attackers: see above "attackers" description                |
|              | -Monitors: see above "monitors" description                  |
|              | -Checkers: see above "checkers" description                  |
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
|step 3        | do checker: check whether the status of application          |
|              | resources on different nodes are updated                     |
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
|post-action   | It is the action when the test cases exist. It will check the|
|              | status of the cluster messaging process(corosync) on the     |
|              | host, and restart the process if it is not running for next  |
|              | test cases                                                   |
+--------------+------+----------------------------------+--------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
+--------------+--------------------------------------------------------------+
