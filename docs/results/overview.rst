.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

Yardstick test tesult document overview
=======================================

.. _`Yardstick user guide`: artifacts.opnfv.org/yardstick/docs/userguide/index.html
.. _Dashboard: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _Jenkins: https://build.opnfv.org/ci/view/yardstick/
.. _Scenarios: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-scenarios

This document provides an overview of the results of test cases developed by
the OPNFV Yardstick Project, executed on OPNFV community labs.

Yardstick project is described in `Yardstick user guide`_.

Yardstick is run systematically at the end of an OPNFV fresh installation.
The system under test (SUT) is installed by the installer Apex, Compass, Fuel
or Joid on Performance Optimized Datacenter (POD); One single installer per
POD. All the runnable test cases are run sequentially. The installer and the
POD are considered to evaluate whether the test case can be run or not. That is
why all the number of test cases may vary from 1 installer to another and from
1 POD to POD.

OPNFV CI provides automated build, deploy and testing for
the software developed in OPNFV. Unless stated, the reported tests are
automated via Jenkins Jobs. Yardsrick test results from OPNFV Continous
Integration can be found in the following dashboard:

* *Yardstick* Dashboard_:  uses influx DB to store Yardstick CI test results and
   Grafana for visualization (user: opnfv/ password: opnfv)

The results of executed test cases are available in Dashboard_ and all logs are
stored in Jenkins_.

It was not possible to execute the entire Yardstick test cases suite on the
PODs assigned for release verification over a longer period of time, due to
continuous work on the software components and blocking faults either on
environment, features or test framework.

The list of scenarios supported by each installer can be described as follows:

+-------------------------+---------+---------+---------+---------+
|         Scenario        |  Apex   | Compass |  Fuel   |   Joid  |
+=========================+=========+=========+=========+=========+
| os-nosdn-nofeature-noha |         |         |    X    |    X    |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-nofeature-ha   |    X    |    X    |    X    |    X    |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-nofeature-ha  |    X    |    X    |    X    |    X    |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-nofeature-noha|         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l3-nofeature-ha  |    X    |    X    |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l3-nofeature-noha|         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-onos-sfc-ha          |    X    |    X    |    X    |    X    |
+-------------------------+---------+---------+---------+---------+
| os-onos-sfc-noha        |         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-onos-nofeature-ha    |    X    |    X    |    X    |    X    |
+-------------------------+---------+---------+---------+---------+
| os-onos-nofeature-noha  |         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-sfc-ha        |         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-sfc-noha      |    X    |    X    |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-bgpvpn-ha     |    X    |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-bgpvpn-noha   |         |    X    |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-kvm-ha         |         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-kvm-noha       |         |    X    |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-ovs-ha         |         |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-ovs-noha       |    X    |         |    X    |         |
+-------------------------+---------+---------+---------+---------+
| os-ocl-nofeature-ha     |         |         |         |         |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-lxd-ha         |         |         |         |    X    |
+-------------------------+---------+---------+---------+---------+
| os-nosdn-lxd-noha       |         |         |         |    X    |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-fdio-noha     |    X    |         |         |         |
+-------------------------+---------+---------+---------+---------+
| os-odl_l2-moon-ha       |         |    X    |         |         |
+-------------------------+---------+---------+---------+---------+

To qualify for release, the scenarios must have deployed and been successfully
tested in four consecutive installations to establish stability of deployment
and feature capability. It is a recommendation to run Yardstick test
cases over a longer period of time in order to better understand the behavior
of the system under test.

References
----------

* IEEE Std 829-2008. "Standard for Software and System Test Documentation".

* OPNFV Colorado release note for Yardstick.
