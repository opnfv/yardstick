TC019
-----
.. add the four sections below for each Test Case in the daily test suite or
   on-demand test cases (HA, KVM, Parser)
This test case verifies the high availability of the openstack service, i.e. "nova-api", on controller node.
There are one attacker, "kill-process" which kills all "nova-api" processes, and two monitors, "openstack-cmd" monitoring "nova-api" service by openstack command "nova image-list", while "process" monitor checks whether "nova-api" process is running. Please see the test case description document for detail.

* Overview of test results
.. general on metrics collected, number of iterations
The service_outage_time of "nova image-list" is 0 seconds, while the process_recover_time of "nova-api" is 300 seconds which equals the running time of this test case, that means the "nova-api" service can't automatiocally recover itself.

* Detailed test results
.. info on lab, installer, scenario
This test case is executed in CMCC's lab with 3+2 HA deployment, where the installer is Arno SR1 release of fuel.

All "nova-api" process on the selected controller node was killed, and results of two monitors were collected. Specifically, the results of "nova image-list" request were collected from compute node and the status of "nova-api" process were collected from the selected controller node.

Each monitor was running in a single process. The running time of each monitor was about 300 seconds with no waiting time between twice monitor running. For "nova image-list", the running times is 127, that's to say there is one openstack command request every 2.36 seconds; while the running times is 141 for "nova-api" process checking, the accurancy is about 2.13 seconds.

The outage time of each monitor, which the name is "service_outage_time" for "openstack-cmd" monitor and "process_recover_time" for "process" monitor, is defined as the duration from the begin time of the first failure request to the end time of the last failure request.

All "nova image-list" requestes were success, so the service_outage_time of "nova image-list" is 0 second, while "nova-api" processes were not running for all "process" checking, so the process_recover_time of "nova-api" is 300 seconds.

* Rationale for decisions
.. pass/fail
fail

* Conclusions and recommendations
.. did the expected behavior occured?
Since the service_outage_time is 0 second, that means the time for the failover is less than 2.36s. Meanwhile, since the process_recover_time equals test case runing time, then it means the process is not automatically recovered, which should be imporved.

Currently, this test case was just runing in Fuel installer. It will be on more installer, such as compass4nfv, apex and joid, with different versiones.


TC025
-----
.. add the four sections below for each Test Case in the daily test suite or
   on-demand test cases (HA, KVM, Parser)
This test case verifies the high availability of controller node. When one of the controller node abnormally shutdown, the service provided by it should be OK.
There are one attacker, "kill-process" which kills all "nova-api" processes, and two "openstack-cmd" monitors, one monitoring openstack command "nova image-list" and the other monitoring "neutron router-list".
Please see the test case description document for detail.

* Overview of test results
.. general on metrics collected, number of iterations
The both service_outage_time of "nova image-list" and "neutron router-list" were 0 second.

* Detailed test results
.. info on lab, installer, scenario
This test case is executed in CMCC's lab with 3+2 HA deployment, where the installer is Arno SR1 release of fuel.

A selected controller node was shutdown, and results of two monitors were collected from compute node.

the return results of "nova image-list" and "neutron router-list" requests from compute node were collected, then the failure requestion time were statistic service_outage_time of corresponding service.

Each monitor was running in a single process. The running time of each monitor was about 300 seconds with no waiting time between twice monitor running. For "nova image-list", the running times is 49, that's to say there is one openstack command request every 6.12 seconds; while the running times is 28 for "neutron router-list", the accurancy is about 10.71 seconds.

The "service_outage_time" for two monitors is defined as the duration from the begin time of the first failure request to the end time of the last failure request.

All "nova image-list" and "neutron router-list" requestes were success, so the service_outage_time of both two monitor were 0 second.

* Rationale for decisions
.. pass/fail
pass

* Conclusions and recommendations
.. did the expected behavior occured?
There was none failure request in this test case running time. However the monitoring times are significantly less than TC019 which kill the "nova-api" service on a selected controller node, and the selected controller node is the same.Therefore it needs more accurate test method.

Currently, this test case was just runing in Fuel installer. It will be on more installer, such as compass4nfv, apex and joid, with different versiones.
