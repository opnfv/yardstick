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
-----
Between test dates, the average measurements for memory bandwidth vary between
22.6 and 29.1 GB/s. Within each test run the results vary more, with a minimal
BW of 20.0 GB/s and maximum of 29.5 GB/s on the totality.
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


Joid
====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD5: https://wiki.opnfv.org/pharos?&#community_test_labs


Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 4 scenario test runs, each run
on the Intel POD5_ between September 11 and 14 in 2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 1.59 and 1.70 ms.
Two test runs have reached the same greater RTT spike of 3.06 ms, which are
1.66 and 1.70 ms average, but only one has the lower RTT of 1.35 ms. The other
two runs have no similar spike at all. To be able to draw conclusions more runs
should be made. SLA set to be 10 ms. The SLA value is used as a reference, it
has not been defined by OPNFV.

TC005
-----
The IO read bandwidth actually refers to the storage throughput and the
greatest IO read bandwidth of the four runs is 173.3 MB/s. The IO read
bandwidth of the four runs looks similar on different four days, with an
average between 32.7 and 60.4 MB/s. One of the runs has a minimum BW of 429
KM/s and other has a maximum BW of 173.3 MB/s. The SLA of read bandwidth sets
to be 400 MB/s, which is used as a reference, and it has not been defined by
OPNFV.

TC010
-----
The tool we use to measure memory read latency is lmbench, which is a series of
micro benchmarks intended to measure basic operating system and hardware system
metrics. The memory read latency of the four runs is 1.1 ns on average. The
variations within each test run are different, some vary from a large range and
others have a small change. For example, the largest change is on September 14,
the memory read latency of which is ranging from 1.12 ns to 1.22 ns. However,
the results on September 12 change very little, which range from 1.14 ns to
1.17 ns. The SLA sets to be 30 ns. The SLA value is used as a reference, it has
not been defined by OPNFV.

TC011
-----
Iperf3 is a tool for evaluating the pocket delay variation between 2 VMs on
different blades. The reported pocket delay variations of the four test runs
differ from each other. The results on September 13 within the date look
similar and the values are between 0.0087 and 0.0190 ms, which is 0.0126 ms on
average. However, on the fourth day, the pocket delay variation has a large
wide change within the date, which ranges from 0.0032 ms to 0.0121 ms and has
the minimum average value. The pocket delay variations of other two test runs
look relatively similar, which are 0.0076 ms and 0.0152 ms on average. The SLA
value sets to be 10 ms. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC012
-----
Lmbench is also used to measure the memory read and write bandwidth, in which
we use bw_mem to obtain the results. Among the four test runs, the memory
bandwidth within the second day almost keep stable, which is 11.58 GB/s on
average. And the memory bandwidth of the fourth day look similar as that of the
second day, both of which remain stable. The other two test runs relatively
change from a large wide range, in which the minimum memory bandwidth is 11.22
GB/s and the maximum bandwidth is 16.65 GB/s with an average bandwidth of about
12.20 GB/s. Here SLA set to be 15 GB/s. The SLA value is used as a reference,
it has not been defined by OPNFV.

TC014
-----
The Unixbench is used to measure processing speed, that is instructions per
second. It can be seen from the dashboard that the processing test results
vary from scores 3272 to 3444, and there is only one result one date. The
overall average score is 3371. No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The mean packet throughput of the four test runs is 119.85, 128.02, 121.40 and
126.08 kpps, of which the result of the second is the highest. The RTT results
of all the test runs keep flat at approx. 37 ms. It is obvious that the PPS
results are not as consistent as the RTT results.

The No. flows of the four test runs are 240 k on average and the PPS results
look a little waved since the largest packet throughput is 184 kpps and the
minimum throughput is 49 K respectively.

There are no errors of packets received in the four runs, but there are still
lost packets in all the test runs. The RTT values obtained by ping of the four
runs have the similar average vaue, that is 38 ms, of which the worest RTT is
93 ms on Sep. 14th.

CPU load of the four test runs have a large change, since the minimum value and
the peak of CPU load is 0 percent and 51 percent respectively. And the best
result is obtained on Sep. 14th.

TC069
-----
With the block size changing from 1 kb to 512 kb, the memory write bandwidth
tends to become larger first and then smaller within every run test, which
rangs from 22.3 GB/s to 26.8 GB/s and then to 18.5 GB/s on average. Since the
test id is one, it is that only the INT memory write bandwidth is tested. On
the whole, when the block size is 8 kb and 16 kb, the memory write bandwidth
look similar with a minimal BW of 22.5 GB/s and peak value of 28.7 GB/s. SLA
sets to be 7 GB/s. The SLA value is used as a a reference, it has not been
defined by OPNFV.

TC070
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other. Within each test run, the maximum RTT can reach
more than 80 ms and the average RTT is usually approx. 38 ms. On the whole, the
average RTTs of the four runs keep flat.

Memory utilization is measured by free, which can display amount of free and
used memory in the system. The largest amount of used memory is 268 MiB on Sep
14, which also has the largest minimum memory. Besides, the rest three test
runs have the similar used memory. On the other hand, the free memory of the
four runs have the same smallest minimum value, that is about 223 MiB, and the
maximum free memory of three runs have the similar result, that is 337 MiB,
except that on Sep. 14th, whose maximum free memory is 254 MiB. On the whole,
all the test runs have similar average free memory.

Network throughput and packet loss can be measured by pktgen, which is a tool
in the network for generating traffic loads for network experiments. The mean
network throughput of the four test runs seem quite different, ranging from
119.85 kpps to 128.02 kpps. The average number of flows in these tests is
24000, and each run has a minimum number of flows of 2 and a maximum number
of flows of 1.001 Mil. At the same time, the corresponding packet throughput
differ between 49.4k and 193.3k with an average packet throughput of approx.
125k. On the whole, the PPS results seem consistent. Within each test run of
the four runs, when number of flows becomes larger, the packet throughput seems
not larger in the meantime.

TC071
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other. Within each test run, the maximum RTT can reach
more than 94 ms and the average RTT is usually approx. 35 ms. On the whole, the
average RTTs of the four runs keep flat.

Cache utilization is measured by cachestat, which can display size of cache and
buffer in the system. Cache utilization statistics are collected during UDP
flows sent between the VMs using pktgen as packet generator tool.The largest
cache size is 212 MiB in the four runs, and the smallest cache size is 75 MiB.
On the whole, the average cache size of the four runs is approx. 208 MiB.
Meanwhile, the tread of the buffer size looks similar with each other.

Packet throughput can be measured by pktgen, which is a tool in the network for
generating traffic loads for network experiments. The mean packet throughput of
the four test runs seem quite different, ranging from 119.85 kpps to 128.02
kpps. The average number of flows in these tests is 239.7k, and each run has a
minimum number of flows of 2 and a maximum number of flows of 1.001 Mil. At the
same time, the corresponding packet throughput differ between 49.4k and 193.3k
with an average packet throughput of approx. 125k. On the whole, the PPS results
seem consistent. Within each test run of the four runs, when number of flows
becomes larger, the packet throughput seems not larger in the meantime.

TC072
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The RTT results are similar throughout the different test dates and runs at
approx. 32 ms. The PPS results are not as consistent as the RTT results.

Network utilization is measured by sar, that is system activity reporter, which
can display the average statistics for the time since the system was started.
Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The largest total number of packets
transmitted per second differs from each other, in which the smallest number of
packets transmitted per second is 6 pps on Sep. 12ed and the largest of that is
210.8 kpps. Meanwhile, the largest total number of packets received per second
differs from each other, in which the smallest number of  packets received per
second is 2 pps on Sep. 13rd and the largest of that is 250.2 kpps.

In some test runs when running with less than approx. 90000 flows the PPS
throughput is normally flatter compared to when running with more flows, after
which the PPS throughput decreases. For the other test runs there is however no
significant change to the PPS throughput when the number of flows are
increased. In some test runs the PPS is also greater with 1000000 flows
compared to other test runs where the PPS result is less with only 2 flows.

There are lost packets reported in most of the test runs. There is no observed
correlation between the amount of flows and the amount of lost packets.
The lost amount of packets normally differs a lot per test run.

Detailed test results
---------------------
The scenario was run on Intel POD5_ with:
Joid
OpenStack Mitaka
OpenVirtualSwitch 2.5.90
OpenDayLight Beryllium

Rationale for decisions
-----------------------
Pass

Conclusions and recommendations
-------------------------------
Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.


