.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Yin Kanglin and others.
.. 14_ykl@tongji.edu.cn

*************************************
Yardstick Test Case Description TC054
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Virtual IP High Availability                                       |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC054: OpenStack Virtual IP High             |
|              | Availability                                                 |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability for virtual |
|              | ip in the environment. When master node of virtual ip is     |
|              | abnormally shutdown, connection to virtual ip and            |
|              | the services binded to the virtual IP it should be OK.       |
+--------------+--------------------------------------------------------------+
|test method   | This test case shutdowns the virtual IP master node with     |
|              | some fault injection tools, then checks whether virtual ips  |
|              | can be pinged and services binded to virtual ip are OK with  |
|              | some monitor tools.                                          |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "control-shutdown" is  |
|              | needed. This attacker includes two parameters:               |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "control-shutdown" in    |
|              | this test case.                                              |
|              | 2) host: which is the name of a control node being attacked. |
|              |                                                              |
|              | In this case the host should be the virtual ip master node,  |
|              | that means the host ip is the virtual ip, for exapmle:       |
|              | -fault_type: "control-shutdown"                              |
|              | -host: node1(the VIP Master node)                            |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, two kinds of monitor are needed:          |
|              | 1. the "ip_status" monitor that pings a specific ip to check |
|              | the connectivity of this ip, which needs two parameters:     |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scripts. It should be always set to "ip_status"  |
|              | for this monitor.                                            |
|              | 2) ip_address: The ip to be pinged. In this case, ip_address |
|              | should be the virtual IP.                                    |
|              |                                                              |
|              | 2. the "openstack-cmd" monitor constantly request a specific |
|              | Openstack command, which needs two parameters:               |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scripts. It should be always set to              |
|              | "openstack-cmd" for this monitor.                            |
|              | 2) command_name: which is the command name used for request. |
|              |                                                              |
|              | e.g.                                                         |
|              | monitor1:                                                    |
|              | -monitor_type: "ip_status"                                   |
|              | -host: 192.168.0.2                                           |
|              | monitor2:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -command_name: "nova image-list"                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there are two metrics:                    |
|              | 1) ping_outage_time: which-indicates the maximum outage time |
|              | to ping the specified host.                                  |
|              | 2)service_outage_time: which indicates the maximum outage    |
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
|              | 1) test case file: opnfv_yardstick_tc054.yaml                |
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
|              | the shutdown script on the VIP master node.                  |
|              |                                                              |
|              | Result: VIP master node will be shutdown                     |
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
|post-action   | It is the action when the test cases exist.  It restarts the |
|              | original VIP master node if it is not restarted.             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
