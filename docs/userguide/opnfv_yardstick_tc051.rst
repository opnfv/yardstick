.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Yin Kanglin and others.
.. 14_ykl@tongji.edu.cn

*************************************
Yardstick Test Case Description TC051
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Controller Node CPU Overload High Availability                     |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC051: OpenStack Controller Node CPU         |
|              | Overload High Availability                                   |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of control  |
|              | node. When the CPU usage of a specified controller node is   |
|              | stressed to 100%, which breaks down the Openstack services   |
|              | on this node. These Openstack service should able to be      |
|              | accessed by other controller nodes, and the services on      |
|              | failed controller node should be isolated.                   |
+--------------+--------------------------------------------------------------+
|test method   | This test case stresses the CPU uasge of a specified control |
|              | node to 100%, then checks whether all services provided by   |
|              | the environment are OK with some monitor tools.              |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "stress-cpu" is        |
|              | needed. This attacker includes two parameters:               |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "stress-cpu" in          |
|              | this test case.                                              |
|              | 2) host: which is the name of a control node being attacked. |
|              | e.g.                                                         |
|              | -fault_type: "stress-cpu"                                    |
|              | -host: node1                                                 |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, the monitor named "openstack-cmd" is      |
|              | needed. The monitor needs needs two parameters:              |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scritps. It should be always set to              |
|              | "openstack-cmd" for this monitor.                            |
|              | 2) command_name: which is the command name used for request  |
|              |                                                              |
|              | There are four instance of the "openstack-cmd" monitor:      |
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
|              | 1) test case file: opnfv_yardstick_tc051.yaml                |
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
|              | the stress cpu script on the host.                           |
|              |                                                              |
|              | Result: The CPU usage of the host will be stressed to 100%.  |
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
|post-action   | It is the action when the test cases exist. It kills the     |
|              | process that stresses the CPU usage.                         |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
