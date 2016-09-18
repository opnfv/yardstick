.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


======================================
Test Results for os-nosdn-nofeature-ha
======================================

.. toctree::
   :maxdepth: 2


apex
====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD1: https://wiki.opnfv.org/pharos?&#community_test_labs


Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 4 scenario test
runs, each run on the LF POD1_ between August 25 and 28 in
2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 0.74 and 1.08 ms.
A few runs start with a 0.99 - 1.07 ms RTT spike (This could be because of
normal ARP handling). One test run has a greater RTT spike of 1.35 ms.
To be able to draw conclusions more runs should be made. SLA set to 10 ms.
The SLA value is used as a reference, it has not been defined by OPNFV.

TC005
-----
The IO read bandwidth looks similar between different dates, with an
average between approx. 128 and 136 MB/s. Within each test run the results
vary, with a minimum 5 MB/s and maximum 446 MB/s on the totality. Most runs
have a minimum BW of 5 MB/s (one run at 6 MB/s). The maximum BW varies more in
absolute numbers between the dates, between 416 and 446 MB/s.
SLA set to 400 MB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC010
-----
The measurements for memory latency are similar between test dates and result
in approx. 1.09 ns. The variations within each test run are similar, between
1.0860 and 1.0880 ns.
SLA set to 30 ns. The SLA value is used as a reference, it has not been defined
by OPNFV.

TC011
-----
Packet delay variation between 2 VMs on different blades is measured using
Iperf3. The reported packet delay variation varies between 0.0025 and 0.0148 ms,
with an average delay variation between 0.0056 ms and 0.0157 ms.

TC012
-----
Between test dates, the average measurements for memory bandwidth result in
approx. 19.70 GB/s. Within each test run the results vary more, with a minimal
BW of 18.16 GB/s and maximum of 20.13 GB/s on the totality.
SLA set to 15 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC014
-----
The Unixbench processor test run results vary between scores 3224.4 and 3842.8,
one result each date. The average score on the total is 3659.5.
No SLA set.

TC037
-----
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

CPU utilization statistics are collected during UDP flows sent between the VMs
using pktgen as packet generator tool. The average measurements for CPU
utilization ratio vary between 1% to 2%. The peak of CPU utilization ratio
appears around 7%.

TC069
Between test dates, the average measurements for memory bandwidth vary between
22.6 and 29.1 GB/s. Within each test run the results vary more, with a minimal
BW of 20.0 GB/s and maximum of 29.5 GB/s on the totality.
SLA set to 6 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.


TC070
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

Memory utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The average measurements for memory
utilization vary between 225MB to 246MB. The peak of memory utilization appears
around 340MB.

TC071
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

Cache utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The average measurements for cache
utilization vary between 205MB to 212MB.

TC072
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

Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. Total number of packets received per
second was average on 200 kpps and total number of packets transmitted per
second was average on 600 kpps.

Detailed test results
---------------------
The scenario was run on LF POD1_ with:
Apex
OpenStack Mitaka
OpenVirtualSwitch 2.5.90
OpenDayLight Beryllium

Rationale for decisions
-----------------------
Pass

Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.

