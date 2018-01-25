+-----------------------------------------------------------------------------+
|HA on VM: Verify VM can self recover after failure                           |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC085: HA on VM-When VM Fails the Alarm is   |
|              | Generated and the VM will Automatically Recover              |
+--------------+--------------------------------------------------------------+
|test purpose  | This test case will verify the high availability of the VM.  |
|              | When the VM occur a panic failure, this test case will       |
|              | observe whether an alarm is generated and the VM has been automatically recovered.     |
|              | (WatchDog recovery behavior: reboot, shutdown, etc.)         |
+--------------+--------------------------------------------------------------+
|test method   | This test case will log in VM and construct the panic        |
|              | failure, and observe whether an alarm is generated and the VM has been automatically   |
|              | recovered.                                                   |
+--------------+--------------------------------------------------------------+
|attackers     | In this test case, an attacker called "vm-attack" is needed. |
|              | This attacker includes two parameters:                       |
|              | 1) fault_type: which is used for finding the attacker's      |
|              | scripts. It should be always set to "vm-attack" in this test |
|              | case.                                                        |
|              | 2) host: the name of vm being attacked.                      |
|              |                                                              |
|              | e.g.                                                         |
|              | -fault_type: "vm-attack"                                     |
|              | -host: vm1                                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|monitors      | In this test case, the following monitors are needed:        |
|              | The "vm-status" monitor will check whether the status of     |
|              | VM will become reboot. This monitor has the following        |
|              | parameters:                                                  |
|              |  - monitor_type: which is used for finding the monitor class |
|              |    and related scritps. It should be always set to           |
|              |    "vm-status" for this monitor;                             |
|              |                                                              |
|              | (e.g.)                                                       |
|              | monitor1:                                                    |
|              | -monitor_type: "vm-status"                                   |
+--------------+--------------------------------------------------------------+
|metrics       | In this test case, there is one metric:                      |
|              | 1)vm_status: which indicates the vm is reboot and            |
|              | automatically recovered.                                     |
|              |                                                              |
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
|              | - Attackers: see above "attackers" description                |
|              | - waiting_time: which is the time (seconds) from the process  |
|              | being killed to stoping monitors the monitors                |
|              | - Monitors: see above "monitors" description                  |
|              | - SLA: see above "metrics" description                        |
|              |                                                              |
|              | 2)POD file: pod.yaml                                         |
|              | The pod.yaml file contains host and login information about   |              
|              | the nodes in the POD. The "nodes" mentioned in this test case |               
|              | description need to be defined in the pod.yaml
|              
|              |           correspondingly.
|              
|              |                                                |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-action    | It is the action before the test case starts, 1)The cloud    |
|              | management system is running. 2)The VM with Soft Dog         |
|              | program (trigger action is reboot) installed has been        |
|              | created.                                                     |
+--------------+--------------------------------------------------------------+
|step 1        | Determine the IP address of the VM through OpenStack
|
|              |                                                              |
|              | Result: The IP of the VM is got.                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | do attacker: Log in VM and construct the panic failure by    |
|              | executing the command "echo c > /proc/sysrq-trigger¡±.        |
|              |                                                              |
|              | Result: The VM will occur a panic failure and then reboot.   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | do monitor: Observe whether the status of the VM is          |
|              | transferred to reboot and has been automatically recovered   |
|              | by Soft Dog.                                                 |
|              |                                                              |
|              | Result: The VM has been automatically recovered.             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|post-action   | It is the action when the test cases exits. It will check    |
|              | the status of the specified process on the host, and restart |
|              | the process if it is not running for next test cases.        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+