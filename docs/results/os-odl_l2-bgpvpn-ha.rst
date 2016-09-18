.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


====================================
Test Results for os-odl_l2-bgpvpn-ha
====================================

.. toctree::
   :maxdepth: 2


fuel
====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD2: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 4 scenario test runs, each run
on the Ericsson POD2_ between September 7 and 11 in 2016.

TC043
-----
The round-trip-time (RTT) between 2 nodes is measured using
ping. Most test run measurements result on average between 0.21 and 0.28 ms.
A few runs start with a 0.32 - 0.35 ms RTT spike (This could be because of
normal ARP handling). To be able to draw conclusions more runs should be made.
SLA set to 10 ms. The SLA value is used as a reference, it has not been defined
by OPNFV.

Detailed test results
---------------------
The scenario was run on Ericsson POD2_ with:
Fuel 9.0
OpenStack Mitaka
OpenVirtualSwitch 2.5.90
OpenDayLight Beryllium

Rationale for decisions
-----------------------
Pass

Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.

