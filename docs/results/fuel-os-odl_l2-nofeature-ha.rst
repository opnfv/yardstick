.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


============================================
Test Results for fuel-os-odl_l2-nofeature-ha
============================================

.. toctree::
   :maxdepth: 2


.. _Grafana: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _POD2: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 6 scenario test
runs, each run on the Ericsson POD2_ between February 13 and 24 in 2016. Test
case TC011_ is the greater exception for which there are only 2 test runs
available, due to earlier problems with InfluxDB test result population.
The best would be to have more runs to draw better conclusions from, but these
are the only runs available at the time of OPNFV R2 release.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 0.3 and 0.5 ms, but
one date (Feb. 23) sticks out with an RTT average of 1 ms.
A few runs start with a 1 - 2 ms RTT spike (This could be because of normal ARP
handling). One test run has a greater RTT spike of 3.9 ms, which is the same
one with the 0.9 ms average. The other runs have no similar spike at all.
To be able to draw conclusions more runs should be made.
SLA set to 10 ms. The SLA value is used as a reference, it has not
been defined by OPNFV.

TC005
-----
The IO read bandwidth looks similar between different dates, with an
average between approx. 165 and 185 GB/s. Within each test run the results
vary, with a minimum 2KB/s and maximum 617KB/s on the totality. Most runs have
a minimum BW of 3KB/s (two runs at 2 KB/s). The maximum BW varies more in
absolute numbers between the dates, between 566 and 617 KB/s.
SLA set to 400KB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC010
-----
The measurements for memory latency are similar between test dates and result
in approx. 1.2 ns. The variations within each test run are similar, between
1.215 and 1.219 ns. One exception is February 16, where the average is 1.222
and varies between 1.22 and 1.28 ns.
SLA set to 30 ns. The SLA value is used as a reference, it has not been defined
by OPNFV.

TC011
-----
Only 2 test runs are available to report results on.

Packet delay variation between 2 VMs on different blades is measured using
Iperf3. On the first date the reported packet delay variation varies between
0.0025 and 0.011 ms, with an average delay variation of 0.0067 ms.
On the second date the delay variation varies between 0.002 and 0.006 ms, with
an average delay variation of 0.004 ms.

TC012
-----
Results are reported for 5 test runs. It is not known why the 6:th test run
is missing.
Between test dates the average measurements for memory bandwidth vary between
17.4 and 17.9 GB/s. Within each test run the results vary more, with a minimal
BW of 16.4 GB/s and maximum of 18.2 GB/s on the totality.
SLA set to 15 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC014
-----
Results are reported for 5 test runs. It is not known why the 6:th test run
is missing.
The Unixbench processor test run results vary between scores 3080 and 3240,
one result each date. The average score on the total is 3150.
No SLA set.

TC037
-----
Results are reported for 5 test runs. It is not currently known why the 6:th
test run is missing.
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The RTT results are similar throughout the different test dates and runs at
approx. 15 ms. Some test runs show an increase with many flows, in the range
towards 16 to 17 ms. One exception standing out is Feb. 15 where the average
RTT is stable at approx. 13 ms. The PPS results are not as consistent as the
RTT results.
In some test runs when running with less than approx. 10000 flows the PPS
throughput is normally flatter compared to when running with more flows, after
which the PPS throughput decreases. Around 20 percent decrease in the worst
case. For the other test runs there is however no significant change to the PPS
throughput when the number of flows are increased. In some test runs the PPS
is also greater with 1000000 flows compared to other test runs where the PPS
result is less with only 2 flows.

The average PPS throughput in the different runs varies between 414000 and
452000 PPS. The total amount of packets in each test run is approx. 7500000 to
8200000 packets. One test run Feb. 15 sticks out with a PPS average of
558000 and approx. 1100000 packets in total (same as the on mentioned earlier
for RTT results).

There are lost packets reported in most of the test runs. There is no observed
correlation between the amount of flows and the amount of lost packets.
The lost amount of packets normally range between 100 and 1000 per test run,
but there are spikes in the range of 10000 lost packets as well, and even
more in a rare cases.

Detailed test results
---------------------
The scenario was run on Ericsson POD2_ with:
Fuel 8.0
OpenStack Liberty
OpenVirtualSwitch 2.3.1
OpenDayLight Beryllium

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
Also of interest could be to see if there are continuous variations where
some test cases stand out with better or worse results than the general test
case.
