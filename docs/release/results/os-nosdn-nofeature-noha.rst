.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


========================================
Test Results for os-nosdn-nofeature-noha
========================================

.. toctree::
   :maxdepth: 2


Joid
=====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD5: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 4 scenario test runs, each run
on the Intel POD5_ between September 12 and 15 in 2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 1.50 and 1.68 ms.
Only one test run has reached greatest RTT spike of 2.92 ms, which has
the smallest RTT of 1.06 ms. The other three runs have no similar spike at all,
the minimum and average RTTs of which are approx. 1.50 ms and 1.68 ms. SLA set to
be 10 ms. The SLA value is used as a reference, it has not been defined by
OPNFV.

TC005
-----
The IO read bandwidth actually refers to the storage throughput, which is
measured by fio and the greatest IO read bandwidth of the four runs is 177.5
MB/s. The IO read bandwidth of the four runs looks similar on different four
days, with an average between 46.7 and 62.5 MB/s. One of the runs has a minimum
BW of 680 KM/s and other has a maximum BW of 177.5 MB/s. The SLA of read
bandwidth sets to be 400 MB/s, which is used as a reference, and it has not
been defined by OPNFV.

The results of storage IOPS for the four runs look similar with each other. The
test runs all have an approx. 1.55 K/s for IO reading with an minimum value of
less than 60 times per second.

TC010
-----
The tool we use to measure memory read latency is lmbench, which is a series of
micro benchmarks intended to measure basic operating system and hardware system
metrics. The memory read latency of the four runs is between 1.134 ns and 1.227
ns on average. The variations within each test run are quite different, some
vary from a large range and others have a small change. For example, the
largest change is on September 15, the memory read latency of which is ranging
from 1.116 ns to 1.393 ns. However, the results on September 12 change very
little, which mainly keep flat and range from 1.124 ns to 1.55 ns. The SLA sets
to be 30 ns. The SLA value is used as a reference, it has not been defined by
OPNFV.

TC011
-----
Iperf3 is a tool for evaluating the pocket delay variation between 2 VMs on
different blades. The reported pocket delay variations of the four test runs
differ from each other. The results on September 13 within the date look
similar and the values are between 0.0213 and 0.0225 ms, which is 0.0217 ms on
average. However, on the third day, the packet delay variation has a large
wide change within the date, which ranges from 0.008 ms to 0.0225 ms and has
the minimum value. On Sep. 12, the packet delay is quite long, for the value is
between 0.0236 and 0.0287 ms and it also has the maximum packet delay of 0.0287
ms. The packet delay of the last test run is 0.0151 ms on average. The SLA
value sets to be 10 ms. The SLA value is used as a reference, it has not been
defined by OPNFV.

TC012
-----
Lmbench is also used to measure the memory read and write bandwidth, in which
we use bw_mem to obtain the results. Among the four test runs, the memory
bandwidth of three test runs almost keep stable within each run, which is
11.65, 11.57 and 11.64 GB/s on average. However, the memory read and write
bandwidth on Sep. 14 has a large range, for it ranges from 11.36 GB/s to 16.68
GB/s. Here SLA set to be 15 GB/s. The SLA value is used as a reference, it has
not been defined by OPNFV.

TC014
-----
The Unixbench is used to evaluate the IaaS processing speed with regards to
score of single cpu running and parallel running. It can be seen from the
dashboard that the processing test results vary from scores 3222 to 3585, and
there is only one result one date. No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The mean packet throughput of the four test runs is 124.8, 160.1, 113.8 and
137.3 kpps, of which the result of the second is the highest. The RTT results
of all the test runs keep flat at approx. 37 ms. It is obvious that the PPS
results are not as consistent as the RTT results.

The No. flows of the four test runs are 240 k on average and the PPS results
look a little waved since the largest packet throughput is 243.1 kpps and the
minimum throughput is 37.6 kpps respectively.

There are no errors of packets received in the four runs, but there are still
lost packets in all the test runs. The RTT values obtained by ping of the four
runs have the similar average vaue, that is between 32 ms and 41 ms, of which
the worest RTT is 155 ms on Sep. 14th.

CPU load is measured by mpstat, and CPU load of the four test runs seem a
little similar, since the minimum value and the peak of CPU load is between 0
percent and 9 percent respectively. And the best result is obtained on Sep.
15th, with an CPU load of nine percent.

TC069
-----
With the block size changing from 1 kb to 512 kb, the memory write bandwidth
tends to become larger first and then smaller within every run test, which
rangs from 22.4 GB/s to 26.5 GB/s and then to 18.6 GB/s on average. Since the
test id is one, it is that only the INT memory write bandwidth is tested. On
the whole, when the block size is 8 kb and 16 kb, the memory write bandwidth
look similar with a minimal BW of 22.5 GB/s and peak value of 28.7 GB/s. And
then with the block size becoming larger, the memory write bandwidth tends to
decrease. SLA sets to be 7 GB/s. The SLA value is used as a a reference, it has
not been defined by OPNFV.

TC070
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of three test runs look
similar with each other, and Within these test runs, the maximum RTT can reach
95 ms and the average RTT is usually approx. 36 ms. The network latency tested
on Sep. 14 shows that it has a peak latency of 155 ms. But on the whole, the
average RTTs of the four runs keep flat.

Memory utilization is measured by free, which can display amount of free and
used memory in the system. The largest amount of used memory is 270 MiB on Sep
13, which also has the smallest minimum memory utilization. Besides, the rest
three test runs have the similar used memory with an average memory usage of
264 MiB. On the other hand, the free memory of the four runs have the same
smallest minimum value, that is about 223 MiB, and the maximum free memory of
three runs have the similar result, that is 226 MiB, except that on Sep. 13th,
whose maximum free memory is 273 MiB. On the whole, all the test runs have
similar average free memory.

Network throughput and packet loss can be measured by pktgen, which is a tool
in the network for generating traffic loads for network experiments. The mean
network throughput of the four test runs seem quite different, ranging from
119.85 kpps to 128.02 kpps. The average number of flows in these tests is
240000, and each run has a minimum number of flows of 2 and a maximum number
of flows of 1.001 Mil. At the same time, the corresponding packet throughput
differ between 38k and 243k with an average packet throughput of approx. 134k.
On the whole, the PPS results seem consistent. Within each test run of the four
runs, when number of flows becomes larger, the packet throughput seems not
larger in the meantime.

TC071
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other. Within each test run, the maximum RTT can reach
79 ms and the average RTT is usually approx. 35 ms. On the whole, the average
RTTs of the four runs keep flat.

Cache utilization is measured by cachestat, which can display size of cache and
buffer in the system. Cache utilization statistics are collected during UDP
flows sent between the VMs using pktgen as packet generator tool.The largest
cache size is 214 MiB in the four runs, and the smallest cache size is 100 MiB.
On the whole, the average cache size of the four runs is approx. 210 MiB.
Meanwhile, the tread of the buffer size looks similar with each other. On the
other hand, the mean buffer size of the four runs keep flat, since they have a
minimum value of approx. 7 MiB and a maximum value of 8 MiB, with an average
value of about 8 MiB.

Packet throughput can be measured by pktgen, which is a tool in the network for
generating traffic loads for network experiments. The mean packet throughput of
the four test runs seem quite different, ranging from 113.8 kpps to 124.8 kpps.
The average number of flows in these tests is 240k, and each run has a minimum
number of flows of 2 and a maximum number of flows of 1.001 Mil. At the same
time, the corresponding packet throughput differ between 47.6k and 243.1k with
an average packet throughput between 113.8k and 160.1k. Within each test run of
the four runs, when number of flows becomes larger, the packet throughput seems
not larger in the meantime.

TC072
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The RTT results are similar throughout the different test dates and runs
between 0 ms and 79 ms with an average leatency of approx. 35 ms. The PPS
results are not as consistent as the RTT results, for the mean packet
throughput of the four runs differ from 113.8 kpps to 124.8 kpps.

Network utilization is measured by sar, that is system activity reporter, which
can display the average statistics for the time since the system was started.
Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The largest total number of packets
transmitted per second look similar on the first three runs with a minimum
number of 10 pps and a maximum number of 97 kpps, except the one on Sep. 15th,
in which the number of packets transmitted per second is 10 pps. Meanwhile, the
largest total number of packets received per second differs from each other,
in which the smallest number of packets received per second is 1 pps and the
largest of that is 276 kpps.

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
