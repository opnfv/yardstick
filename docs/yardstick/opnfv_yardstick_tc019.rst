.. image:: ../../etc/opnfv-logo.png
  :height: 40
  :width: 200
  :alt: OPNFV
  :align: left

*************************************
Yardstick Test Case Description TC019
*************************************

+-----------------------------------------------------------------------------+
|OpenStack Controller Service High Availability                               |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC019_HA: Control node Openstack service down|
+--------------+--------------------------------------------------------------+
|metric        | service outage time, process is recovered                    |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of          |
|              | the service provided by OpenStack (like nova-api,            |
|              | neutro-server).                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc019.yaml                             |
|              |                                                              |
|              | *Attackers:                                                  |
|              | -fault_type: "kill-process"  # the fault injection method.   |
|              | -process_name: "nova-api"                                    |
|              | -fault_time: 10  # after 10 minitues, the fault will be      |
|              |                    recovered if not self-recovered           |
|              | -host: node1 # controller node where the process is killed   |
|              | *Monitors:                                                   |
|              | -monitor_type: "openstack-api" # the monitor method. Such as:|
|              |         "openstack-api" will request the openstack API;      |
|              |         "process" will check the process status              |
|              | -api_name: "nova image-list"                                 |
|              | -process_name: "nova-api"                                    |
|              | -host: node1 # the node where the monitor runs               |
|              | *SLA:                                                        |
|              | -outage_time: 5 # the maximum outage time of API request     |
|              | -process_recover: True # the process must be self-recovery   |
+--------------+--------------------------------------------------------------+
|test tool     | None. Self-developed.                                        |
+--------------+--------------------------------------------------------------+
|references    | ETSI NFV REL001                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with multiple different attackers and |
|              | multiple different monitors.                                 |
|              | For each attacker, "fault_type", "fault_time" and "host" are |
|              | common fields; "process_name" is related to "fault_type".    |
|              | For each monitor, "monitor_type" is needed, "api_name" and   |
|              | "process_name" are related to "monitor_type". If "host" is   |
|              | not defined, the monitor will be run where the yardstick     |
|              | framework run                                                |
+--------------+--------------------------------------------------------------+
|pre-test      | The POD configuration should record on pod.yaml first.       |
|conditions    | the "host" item in this test case should use the node name   |
|              | in the pod.yaml.                                             |
+--------------+------+----------------------------------+--------------------+
|test sequence | step | description                      | result             |
|              +------+----------------------------------+--------------------+
|              |  1   | check the SUT enviroment.        |                    |
|              |      | (e.g. whether "nova-api" process |                    |
|              |      | is running)                      |                    |
|              +------+----------------------------------+--------------------+
|              |  2   | run monitors with multiple       | the monitor info   |
|              |      | processes. (e.g. one monitor to  | will be collected  |
|              |      | request "nova image-list",       |                    |
|              |      | one monitor to check the         |                    |
|              |      | "nova-api" is running)           |                    |
|              +------+----------------------------------+--------------------+
|              |  3   | inject faults and then recover   | the specified      |
|              |      | the enviroment if the faults are | process will be    |
|              |      | not self-recoverd within         | killed and then be |
|              |      | specified time                   | recovered          |
|              +------+----------------------------------+--------------------+
|              |  4   | stop monitors and verify the SLA | the test case is   |
|              |      |                                  | passed or not      |
+--------------+------+----------------------------------+--------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
+--------------+--------------------------------------------------------------+
