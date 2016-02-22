.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


===========================================
Test Results for fuel-os-nosdn-nofeature-ha
===========================================

.. toctree::
   :maxdepth: 2


Details
=======

.. _Grafana: http://130.211.154.108/grafana/dashboard/db/yardstick-main

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on at least 4 consequtive
scenario test runs each.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. The measurements are fairly consistent at approx. 1 ms. SLA set to 10 ms.

TC005
-----
The IO read bandwidth is very consistent between different test runs, but
within each run the results vary between 3KB/s and 575KB/s. SLA set to 400KB/s.

TC010
-----
The measurements for memory latency are consistent among test runs and results
in approx. 1,2 ns. SLA set to 30 ns.

TC011
-----
<TBD: None available yet>

TC012
-----
The measurements for memory bandwidth are fairly consistent among different
test runs, but within each run the results vary between 16 and 18 GB/s.
SLA set to 15 GB/s.

TC014
-----
The Unixbench processor single and parallel speed score show the same results
and are fairly stable at approx. 32000. The runs vary between scores 31600 and
32400. No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs are typically affected by
the amount of flows set up and result in higher RTT and less PPS
throughput.

When running with less than 10000 flows the results are flat and consistent.
RTT is then approx. 30 ms and the number of PPS remains flat at approx.
250000 PPS. Beyond approx. 10000 flows and up to 1000000 (one million) there
is an even drop in RTT and PPS performance, eventually ending up at approx.
150-250 ms and 40000 PPS respectively.

Detailed test results
---------------------

.. info on lab, installer, scenario

.. TBD?: More lab details? SW/HW versions?

The scenario is run in Ericsson POD2 lab using Fuel as installer of OpenStack.
The vanilla (non-OPNFV) OVS variant is included in the scenario.
No ODL controller is installed.

Rationale for decisions
-----------------------
.. result analysis, pass/fail

<TBD>

Conclusions and recommendations
-------------------------------

.. did the expected behavior occur?

<TBD>
