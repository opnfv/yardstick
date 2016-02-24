.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


==========================================
Test Results for fuel-os-onos-nofeature-ha
==========================================

.. toctree::
   :maxdepth: 2


Details
=======

.. _Grafana: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _POD2: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 7 scenario test
runs, each run on the Ericsson POD2_ between February 13 and 21 in 2016. Test
case TC011_ is not reported on due to an InfluxDB issue.
The best would be to have more runs to draw better conclusions from, but these
are the only runs available at the time of OPNFV R2 release.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. The majority (5) of the test run measurements result in an average
between 0.4 and 0.5 ms. The other 2 dates stick out with an RTT average of 0.9
to 1 ms.
The majority of the runs start with a 1 - 1.5 ms RTT spike (This could be
because of normal ARP handling). One test run has a greater RTT spike of 4 ms,
which is the same one with the 1 ms RTT average. The other runs have no similar
spike at all. To be able to draw conclusions more runs should be made.
SLA set to 10 ms. The SLA value is used as a reference, it has not
been defined by OPNFV.

TC005
-----
The IO read bandwidth looks similar between different dates, with an
average between approx. 170 and 185 MB/s. Within each test run the results
vary, with a minimum of 2 MB/s and maximum of 690MB/s on the totality. Most
runs have a minimum BW of 3 MB/s (one run at 2 MB/s). The maximum BW varies
more in absolute numbers between the dates, between 560 and 690 MB/s.
SLA set to 400 MB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC010
-----
The measurements for memory latency are similar between test dates and result
in a little less average than 1.22 ns. The variations within each test run are
similar, between 1.213 and 1.226 ns. One exception is the first date, where the
average is 1.223 and varies between 1.215 and 1.275 ns.
SLA set to 30 ns. The SLA value is used as a reference, it has not been defined
by OPNFV.

TC011
-----
For this scenario no results are available to report on. Reason is an
integer/floating point issue regarding how InfluxDB is populated with
result data from the test runs. The issue was fixed but not in time to produce
input for this report.

TC012
-----
Between test dates the average measurements for memory bandwidth vary between
17.1 and 18.1 GB/s. Within each test run the results vary more, with a minimal
BW of 15.5 GB/s and maximum of 18.2 GB/s on the totality.
SLA set to 15 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC014
-----
The Unixbench processor test run results vary between scores 3100 and 3260,
one result each date. The average score on the total is 3170.
No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

There seems to be mainly two result types. One type a high and flatter
PPS throughput not very much affected by the number of flows. Here also the
average RTT is stable around 13 ms throughout all the test runs.

The second type starts with a slightly lower PPS in the beginning than type
one, and decreases even further when passing approx. 10000 flows. Here also the
average RTT tends to start at approx. 15 ms ending with an average of 17 to 18
ms with the maximum amount of flows running.

Result type one can with the maximum amount of flows have a greater PPS than
the second type with the minimum amount of flows.

For result type one the average PPS throughput in the different runs varies
between 399000 and 447000 PPS. The total amount of packets in each test run
is between approx. 7000000 and 10200000 packets.
The second result type has a PPS average of between 602000 and 621000 PPS and a
total packet amount between 10900000 and 13500000 packets.

There are lost packets reported in many of the test runs. There is no observed
correlation between the amount of flows and the amount of lost packets.
The lost amount of packets normally range between 100 and 1000 per test run,
but there are spikes in the range of 10000 lost packets as well, and even
more in a rare cases. Some case is in the range of one million lost packets.

Detailed test results
---------------------
The scenario was run on Ericsson POD2_ with:
Fuel 8.0
OpenStack Liberty
OpenVirtualSwitch 2.3.1
OpenNetworkOperatingSystem Drake

Rationale for decisions
-----------------------
Pass

Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.

Conclusions and recommendations
-------------------------------
The pktgen test configuration has a relatively large base effect on RTT in
TC037 compared to TC002, where there is no background load at all. Approx.
15 ms compared to approx. 0.5 ms, which is more than a 3000 percentage
difference in RTT results.
Especially RTT and throughput come out with better results than for instance
the *fuel-os-nosdn-nofeature-ha* scenario does. The reason for this should
probably be further analyzed and understood. Also of interest could be
to make further analyzes to find patterns and reasons for lost traffic.
Also of interest could be to see why there are variations in some test cases,
especially visible in TC037.

