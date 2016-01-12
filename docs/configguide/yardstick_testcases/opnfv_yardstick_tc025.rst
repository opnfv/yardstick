.. image:: ../../etc/opnfv-logo.png
  :height: 40
  :width: 200
  :alt: OPNFV
  :align: left

*************************************
Yardstick Test Case Description TC025
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Controll Node abnormally shutdown High Availability                |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC025_HA: OpenStack Controll Node abnormally |
|              | shutdown                                                     |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of control  |
|              | nodethe. When one of the control node abnormally shutdown,   |
|              | the service provided by it should be OK.                     |
+--------------+--------------------------------------------------------------+
|test method   | This test case shutdowns a specified control node with some  |
|              | fault injection tools, then checks whether all services      |
|              | provided by the control node are OK with some monitor tools. |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "host-shutdown" is     |
|              | needed. This attacker includes two parameters:               |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "host-shutdown" in       |
|              | this test case.                                              |
|              | 2) host: which is the name of a control node being attacked. |
|              |                                                              |
|              | e.g.                                                         |
|              | -fault_type: "host-shutdown"                                 |
|              | -host: node1                                                 |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, one kind of monitor are needed:           |
|              | 1. the "openstack-cmd" monitor constantly request a specific |
|              |    Openstack command, which needs two parameters             |
|              | 1) monitor_type: which is used for finding the monitor class |
|              | and related scritps. It should be always set to              |
|              | "openstack-cmd" for this monitor.                            |
|              | 2) command_name: which is the command name used for request  |
|              |                                                              |
|              | There are four instance of the "openstack-cmd" monitor:      |
|              | monitor1:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -api_name: "nova image-list"                                 |
|              | monitor2:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -api_name: "neutron router-list"                             |
|              | monitor3:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -api_name: "heat stack-list"                                 |
|              | monitor4:                                                    |
|              | -monitor_type: "openstack-cmd"                               |
|              | -api_name: "cinder list"                                     |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there is one metric:                      |
|              | 1)service_outage_time: which indicates the maximum outage    |
|              | time (seconds) of the specified Openstack command request.   |
+--------------+--------------------------------------------------------------+
|test tool     | None. Self-developed.                                        |
+--------------+--------------------------------------------------------------+
|references    | ETSI NFV REL001                                              |
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
+--------------+------+----------------------------------+--------------------+
|test sequence | step | description                      | result             |
|              +------+----------------------------------+--------------------+
|              |  1   | start monitors: each monitor will| The monitor info   |
|              |      | run with independently process   | will be collected. |
|              +------+----------------------------------+--------------------+
|              |  2   | do attacker: connect the host    | the host will be   |
|              |      | through SSH, and then execute    | shutdown.          |
|              |      | shutdown script on the host      |                    |
|              +------+----------------------------------+--------------------+
|              |  3   | stop monitors after a period of  | All monitor result |
|              |      | time specified by "waiting_time" | will be aggregated.|
|              +------+----------------------------------+--------------------+
|              |  4   | verify the SLA                   | The test case is   |
|              |      |                                  | passed or not.     |
+--------------+------+----------------------------------+--------------------+
|post-action   | It is the action when the test cases exist. It restarts the  |
|              | specified control node if it is not restarted.               |
+--------------+------+----------------------------------+--------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
+--------------+--------------------------------------------------------------+
