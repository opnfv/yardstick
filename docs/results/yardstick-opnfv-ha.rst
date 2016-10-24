.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


===================================
Test Results for yardstick-opnfv-ha
===================================

.. toctree::
   :maxdepth: 2

Details
=======
There are two test cases, TC019 and TC025, for high availability (HA) test of
OPNFV platform, and both test cases were executed in CMCC's lab with 3+2 HA
deployment, where the installer is Arno SR1 release of fuel.


TC019
-----
This test case verifies the high availability of the openstack service, i.e.
"nova-api", on controller node.
There are one attacker, "kill-process" which kills all "nova-api" processes,
and two monitors, "openstack-cmd" monitoring "nova-api" service by openstack
command "nova image-list", while "process" monitor checks whether "nova-api"
process is running. Please see the test case description document for detail.

Overview of test results
------------------------
The service_outage_time of "nova image-list" is 0 seconds, while the
process_recover_time of "nova-api" is 300 seconds which equals the running time
of this test case, that means the "nova-api" service can't automatiocally
recover itself.

Detailed test results
---------------------
All "nova-api" process on the selected controller node was killed, and results
of two monitors were collected. Specifically, the results of "nova image-list"
request were collected from compute node and the status of "nova-api" process
were collected from the selected controller node.

Each monitor was running in a single process. The running time of each monitor
was about 300 seconds with no waiting time between twice monitor running. For
"nova image-list", the running times is 127, that's to say there is one
openstack command request every 2.36 seconds; while the running times is 141
for "nova-api" process checking, the accurancy is about 2.13 seconds.

The outage time of each monitor, which the name is "service_outage_time" for
"openstack-cmd" monitor and "process_recover_time" for "process" monitor, is
defined as the duration from the begin time of the first failure request to the
end time of the last failure request.

All "nova image-list" requestes were success, so the service_outage_time of
"nova image-list" is 0 second, while "nova-api" processes were not running for
all "process" checking, so the process_recover_time of "nova-api" is 300s.

Rationale for decisions
-----------------------
The service_outage_time is 0 second, that means the failover time of openstack
service is less than 2.36s, which is the period of each request. However, the
process_recover_time equals test case runing time, that means the process is
not automatically recovered, so this test case is fail.


TC025
-----
This test case verifies the high availability of controller node. When one of
the controller node abnormally shutdown, the service provided should be OK.
There are one attacker, "kill-process" which kills all "nova-api" processes,
and two "openstack-cmd" monitors, one monitoring openstack command
"nova image-list" and the other monitoring "neutron router-list".
Please see the test case description document for detail.

Overview of test results
------------------------
The both service_outage_time of "nova image-list" and "neutron router-list"
were 0 second.

Detailed test results
---------------------
A selected controller node was shutdown, and results of two monitors were
collected from compute node.

The return results of "nova image-list" and "neutron router-list" requests from
compute node were collected, then the failure requestion time were statistic
service_outage_time of corresponding service.

Each monitor was running in a single process. The running time of each monitor
was about 300 seconds with no waiting time between twice monitor running. For
"nova image-list", the running times is 49, that's to say there is one
openstack command request every 6.12 seconds; while the running times is 28 for
"neutron router-list", the accurancy is about 10.71 seconds.

The "service_outage_time" for two monitors is defined as the duration from the
begin time of the first failure request to the end time of the last failure
request.

All "nova image-list" and "neutron router-list" requestes were success, so the
service_outage_time of both two monitor were 0 second.

Rationale for decisions
-----------------------
As service_outage_time of all monitors are 0 second, that means there are none
failure request in this test case running time, this test case is passed.


Conclusions and recommendations
-------------------------------
The TC019 shows the killed process will be not automatically recovered, which
should be imporved.

There are several improvement points for HA test:
a) Running test cases in different enveriment deployed by different installers,
such as compass4nfv, apex and joid, with different versiones.
b) The period of each request is a little long, it needs more accurate test
method.
c) More test cases with different faults and different monitors are needed.
