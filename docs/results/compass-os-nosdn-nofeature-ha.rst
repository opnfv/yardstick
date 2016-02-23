.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


==============================================
Test Results for compass-os-nosdn-nofeature-ha
==============================================

.. toctree::
   :maxdepth: 2


Details
=======

.. _Grafana: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _SC_POD: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 5 consecutive scenario test
runs, each run on the Huawei SC_POD_ between February 13 and 18 in 2016. The
best would be to have more runs to draw better conclusions from, but these are
the only runs available at the time of OPNFV R2 release

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. The measurements are on average varying between 1.95 and 2.23 ms
with a first 2 - 3.27 ms RTT spike in the beginning of each run (This could be
because of normal ARP handling).SLA set to 10 ms. The SLA value is used as a
reference, it has not been defined by OPNFV.

TC005
-----
The IO read bandwidth look similar between different test runs, with an
average at approx. 145-162 MB/s. Within each run the results vary much,
minimum 2MB/s and maximum 712MB/s on the totality.
SLA set to 400KB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC010
-----
The measurements for memory latency are consistent among test runs and results
in approx. 1.2 ns. The variations between runs are similar, between
1.215 and 1.278 ns.  SLA set to 30 ns. The SLA value is used as
a reference, it has not been defined by OPNFV.

TC011
-----
For this scenario no results are available to report on. Probable reason is
an integer/floating point issue regarding how InfluxDB is populated with
result data from the test runs.

TC012
-----
The average measurements for memory bandwidth are consistent among most of the
different test runs at 12.98 - 16.73 GB/s. The last test run averages at
16.67 GB/s. Within each run the results vary, with minimal BW of 16.59
GB/s and maximum of 16.71 GB/s of the totality.
SLA set to 15 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC014
-----
The Unixbench processor single and parallel speed scores show similar results
at approx. 3000. The runs vary between scores 2499 and 3105.
No SLA set.

TC027
-----
The round-trip-time (RTT) between VM1 with ipv6 router on different blades is
measured using ping6. The measurements are consistent at approx. 4 ms.
SLA set to 30 ms.The SLA value is used as a reference, it has not been
defined by OPNFV.

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
230000 PPS. Beyond approx. 10000 flows and up to 1000000 (one million) there
is an even drop in RTT and PPS performance, eventually ending up at approx.
105-113 ms and 100000 PPS respectively.

TC040
-----
test purpose is to verify the function of Yang-to-Tosca in Parse, and this test
case is a weekly task, so it was triggered by manually, the result whether the
output is same with expected outcome is success
No SLA set.

Detailed test results
---------------------

The scenario was run on Huawei SC_POD_ with:
Compass 1.0
OpenStack Liberty
OVS 2.4.0

No SDN controller installed

Rationale for decisions
-----------------------
Pass

Tests were successfully executed and metrics collects (apart from TC011_).
No SLA was verified. To be decided on in next release of OPNFV.

Conclusions and recommendations
-------------------------------

The pktgen test configuration has a relatively large base effect on RTT in
TC037 compared to TC002, where there is no background load at all (30 ms
compared to 1 ms or less, which is more than a 3000 percentage different
in RTT results). The larger amounts of flows in TC037 generate worse
RTT results, in the magnitude of several hundreds of milliseconds. It would
be interesting to also make and compare all these measurements to completely
(optimized) bare metal machines running native Linux with all other relevant
tools available, e.g. lmbench, pktgen etc.
