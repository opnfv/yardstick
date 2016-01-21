TC019
-----
.. add the four sections below for each Test Case in the daily test suite or
   on-demand test cases (HA, KVM, Parser)
This test case verifies the high availability of the openstack service, i.e. "nova-api", on controller node.

* Overview of test results
.. general on metrics collected, number of iterations
The service_outage_time of "nova image-list" is 0, while the process_recover_time of "nova-api" is 300 seconds which the duration of this test case.

* Detailed test results
.. info on lab, installer, scenario
This test case is executed in CMCC's lab, where the installer is fuel.
The "nova-api" process on one selected controller node was killed, and the return results of "nova image-list" request from compute node and status of "nova-api" process on the selected controller node were collected, then the failure time of request is service_outage_time and the duration from the process was killed to recovered is the process_recover_time.

* Rationale for decisions
.. pass/fail
fail

* Conclusions and recommendations
.. did the expected behavior occured?
The installer needs monitor the openstack service and recover it when the process of the service exit because of some faults.

TC025
-----
.. add the four sections below for each Test Case in the daily test suite or
   on-demand test cases (HA, KVM, Parser)
This test case verifies the high availability of controller node. When one of the controller node abnormally shutdown, the service provided by it should be OK.

* Overview of test results
.. general on metrics collected, number of iterations
The both service_outage_time of "nova image-list" and "neutron router-list" are 0.

* Detailed test results
.. info on lab, installer, scenario
This test case is executed in CMCC's lab, where the installer is fuel.
A selected controller node was shutdown, and the return results of "nova image-list" and "neutron router-list" requests from compute node were collected, then the failure requestion time were statistic service_outage_time of corresponding service.

* Rationale for decisions
.. pass/fail
pass

* Conclusions and recommendations
.. did the expected behavior occured?
None
