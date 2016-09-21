.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


===============================
Test Results for os-onos-sfc-ha
===============================

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
on the Ericsson POD2_ or LF POD2_ between September 5 and 10 in 2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 0.5 and 0.6 ms.
A few runs start with a 1 - 1.5 ms RTT spike (This could be because of normal ARP
handling). One test run has a greater RTT spike of 1.9 ms, which is the same
one with the 0.7 ms average. The other runs have no similar spike at all.
To be able to draw conclusions more runs should be made.
SLA set to 10 ms. The SLA value is used as a reference, it has not
been defined by OPNFV.

TC005
-----
The IO read bandwidth looks similar between different dates, with an
average between approx. 170 and 200 MB/s. Within each test run the results
vary, with a minimum 2 MB/s and maximum 838 MB/s on the totality. Most runs
have a minimum BW of 3 MB/s (two runs at 2 MB/s). The maximum BW varies more in
absolute numbers between the dates, between 617 and 838 MB/s.
SLA set to 400 MB/s. The SLA value is used as a reference, it has not been
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
Packet delay variation between 2 VMs on different blades is measured using
Iperf3. On the first date the reported packet delay variation varies between
0.0025 and 0.011 ms, with an average delay variation of 0.0067 ms.
On the second date the delay variation varies between 0.002 and 0.006 ms, with
an average delay variation of 0.004 ms.

TC012
-----
Between test dates, the average measurements for memory bandwidth vary between
17.4 and 17.9 GB/s. Within each test run the results vary more, with a minimal
BW of 16.4 GB/s and maximum of 18.2 GB/s on the totality.
SLA set to 15 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC014
-----
The Unixbench processor test run results vary between scores 3080 and 3240,
one result each date. The average score on the total is 3150.
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
-----
Between test dates, the average measurements for memory bandwidth vary between
15.5 and 25.4 GB/s. Within each test run the results vary more, with a minimal
BW of 9.7 GB/s and maximum of 29.5 GB/s on the totality.
SLA set to 6 GB/s. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC070
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

Memory utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The average measurements for memory
utilization vary between 225MB to 246MB. The peak of memory utilization appears
around 340MB.

TC071
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

Cache utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The average measurements for cache
utilization vary between 205MB to 212MB.

TC072
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

Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. Total number of packets received per
second was average on 200 kpps and total number of packets transmitted per
second was average on 600 kpps.

Detailed test results
---------------------
The scenario was run on Ericsson POD2_ and LF POD2_ with:
Fuel 9.0
OpenStack Mitaka
Onos Goldeneye
OpenVirtualSwitch 2.5.90
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


Joid
=====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD6: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 4 scenario test runs, each run
on the Intel POD6_ between September 8 and 11 in 2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 1.35 ms and 1.57 ms.
Only one test run has reached greatest RTT spike of 2.58 ms. Meanwhile, the
smallest network latency is 1.11 ms, which is obtained on Sep. 11st. In
general, the average of network latency of the four test runs are between 1.35
ms and 1.57 ms. SLA set to be 10 ms. The SLA value is used as a reference, it
has not been defined by OPNFV.

TC005
-----
The IO read bandwidth actually refers to the storage throughput, which is
measured by fio and the greatest IO read bandwidth of the four runs is 175.4
MB/s. The IO read bandwidth of the three runs looks similar, with an average
between 43.7 and 56.3 MB/s, except one on Sep. 8, for its maximum storage
throughput is only 107.9 MB/s. One of the runs has a minimum BW of 478 KM/s and
other has a maximum BW of 168.6 MB/s. The SLA of read bandwidth sets to be
400 MB/s, which is used as a reference, and it has not been defined by OPNFV.

The results of storage IOPS for the four runs look similar with each other. The
IO read times per second of the four test runs have an average value between
978 per second and 1.20 K/s, and meanwhile, the minimum result is only 36 times
per second.

TC010
-----
The tool we use to measure memory read latency is lmbench, which is a series of
micro benchmarks intended to measure basic operating system and hardware system
metrics. The memory read latency of the four runs is between 1.164 ns and 1.244
ns on average. The variations within each test run are quite different, some
vary from a large range and others have a small change. For example, the
largest change is on September 10, the memory read latency of which is ranging
from 1.128 ns to 1.381 ns. However, the results on September 11 change very
little. The SLA sets to be 30 ns. The SLA value is used as a reference, it has
not been defined by OPNFV.

TC011
-----
Iperf3 is a tool for evaluating the packet delay variation between 2 VMs on
different blades. The reported packet delay variations of the four test runs
differ from each other. In general, the packet delay of two runs look similar,
for they both stay stable within each run. And the mean packet delay of them
are 0.0772 ms and 0.0788 ms respectively. Of the four runs, the fourth has the
worst result, because the packet delay reaches 0.0838 ms. The rest one has a
large wide range from 0.0666 ms to 0.0798 ms. The SLA value sets to be 10 ms.
The SLA value is used as a reference, it has not been defined by OPNFV.

TC012
-----
Lmbench is also used to measure the memory read and write bandwidth, in which
we use bw_mem to obtain the results. Among the four test runs, the trend of the
memory bandwidth almost look similar, which all have a large wide range, and
the minimum and maximum results are 9.02 GB/s and 18.14 GB/s. Here SLA set to
be 15 GB/s. The SLA value is used as a reference, it has not been defined by
OPNFV.

TC014
-----
The Unixbench is used to evaluate the IaaS processing speed with regards to
score of single cpu running and parallel running. It can be seen from the
dashboard that the processing test results vary from scores 3395 to 3475, and
there is only one result one date. No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The mean packet throughput of the four test runs is between 362.1 kpps and
363.5 kpps, of which the result of the third run is the highest. The RTT
results of all the test runs keep flat at approx. 17 ms. It is obvious that the
PPS results are not as consistent as the RTT results.

The No. flows of the four test runs are 240 k on average and the PPS results
look a little waved since the largest packet throughput is 418.1 kpps and the
minimum throughput is 326.5 kpps respectively.

There are no errors of packets received in the four runs, but there are still
lost packets in all the test runs. The RTT values obtained by ping of the four
runs have the similar average vaue, that is approx. 17 ms, of which the worst
RTT is 39 ms on Sep. 11st.

CPU load is measured by mpstat, and CPU load of the four test runs seem a
little similar, since the minimum value and the peak of CPU load is between 0
percent and nine percent respectively. And the best result is obtained on Sep.
10, with an CPU load of nine percent.

TC069
-----
With the block size changing from 1 kb to 512 kb, the memory write bandwidth
tends to become larger first and then smaller within every run test, which
rangs from 25.9 GB/s to 26.6 GB/s and then to 18.1 GB/s on average. Since the
test id is one, it is that only the INT memory write bandwidth is tested. On
the whole, when the block size is from 2 kb to 16 kb, the memory write
bandwidth look similar with a minimal BW of 22.1 GB/s and peak value of 28.6
GB/s. And then with the block size becoming larger, the memory write bandwidth
tends to decrease. SLA sets to be 7 GB/s. The SLA value is used as a reference,
it has not been defined by OPNFV.

TC070
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other, and within these test runs, the maximum RTT can
reach 39 ms and the average RTT is usually approx. 17 ms. The network latency
tested on Sep. 11 shows that it has a peak latency of 39 ms. But on the whole,
the average RTTs of the five runs keep flat and the network latency is
relatively short.

Memory utilization is measured by free, which can display amount of free and
used memory in the system. The largest amount of used memory is 270 MiB on the
first two runs. In general, the mean used memory of two test runs have very
large memory utilization, which can reach 264 MiB on average. And the other two
runs have a large wide range of memory usage with the minimum value of 150 MiB
and the maximum value of 270 MiB. On the other hand, for the mean free memory,
the four test runs have the similar trend with that of the mean used memory.
In general, the mean free memory change from 220 MiB to 342 MiB.

Packet throughput and packet loss can be measured by pktgen, which is a tool
in the network for generating traffic loads for network experiments. The mean
packet throughput of the four test runs seem quite different, ranging from
326.5 kpps to 418.1 kpps. The average number of flows in these tests is
240000, and each run has a minimum number of flows of 2 and a maximum number
of flows of 1.001 Mil. At the same time, the corresponding packet throughput
differ between 326.5 kpps and 418.1 kpps with an average packet throughput between
361.7 kpps and 363.5 kpps. In summary, the PPS results seem consistent. Within each
test run of the four runs, when number of flows becomes larger, the packet
throughput seems not larger at the same time.

TC071
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other. Within each test run, the maximum RTT is only 47
ms and the average RTT is usually approx. 15 ms. On the whole, the average
RTTs of the four runs keep stable and the network latency is relatively small.

Cache utilization is measured by cachestat, which can display size of cache and
buffer in the system. Cache utilization statistics are collected during UDP
flows sent between the VMs using pktgen as packet generator tool. The largest
cache size is 214 MiB, which is same for the four runs, and the smallest cache
size is 94 MiB. On the whole, the average cache size of the four runs look the
same and is between 198 MiB and 207 MiB. Meanwhile, the tread of the buffer
size keep flat, since they have a minimum value of 7 MiB and a maximum value of
8 MiB, with an average value of about 7.9 MiB.

Packet throughput can be measured by pktgen, which is a tool in the network for
generating traffic loads for network experiments. The mean packet throughput of
the four test runs seem quite the same, which is approx. 363 kpps. The average
number of flows in these tests is 240k, and each run has a minimum number of
flows of 2 and a maximum number of flows of 1.001 Mil. At the same time, the
corresponding packet throughput differ between 327 kpps and 418 kpps with an
average packet throughput of about 363 kpps. Within each test run of the four
runs, when number of flows becomes larger, the packet throughput seems not
larger in the meantime.

TC072
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The RTT results are similar throughout the different test dates and runs
between 0 ms and 47 ms with an average leatency of less than 16 ms. The PPS
results are not as consistent as the RTT results, for the mean packet
throughput of the four runs differ from 361.7 kpps to 365.0 kpps.

Network utilization is measured by sar, that is system activity reporter, which
can display the average statistics for the time since the system was started.
Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The largest total number of packets
transmitted per second look similar for two test runs, whose values change a
lot from 10 pps to 432 kpps. While results of the other test runs seem the same
and keep stable with the average number of packets transmitted per second of 10
pps. However, the total number of packets received per second of the four runs
look similar, which have a large wide range of 2 pps to 657 kpps.

In some test runs when running with less than approx. 250000 flows the PPS
throughput is normally flatter compared to when running with more flows, after
which the PPS throughput decreases. For the other test runs there is however no
significant change to the PPS throughput when the number of flows are
increased. In some test runs the PPS is also greater with 250000 flows
compared to other test runs where the PPS result is less with only 2 flows.

There are lost packets reported in most of the test runs. There is no observed
correlation between the amount of flows and the amount of lost packets.
The lost amount of packets normally differs a lot per test run.

Detailed test results
---------------------
The scenario was run on Intel POD6_ with:
Joid
OpenStack Mitaka
Onos Goldeneye
OpenVirtualSwitch 2.5.90
OpenDayLight Beryllium

Rationale for decisions
-----------------------
Pass

Conclusions and recommendations
-------------------------------
Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.

