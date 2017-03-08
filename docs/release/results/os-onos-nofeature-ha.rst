.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


======================================
Test Results for os-onos-nofeature-ha
======================================

.. toctree::
   :maxdepth: 2


Joid
=====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD6: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 5 scenario test runs, each run
on the Intel POD6_ between September 13 and 16 in 2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 1.50 and 1.68 ms.
Only one test run has reached greatest RTT spike of 2.62 ms, which has
the smallest RTT of 1.00 ms. The other four runs have no similar spike at all,
the minimum and average RTTs of which are approx. 1.06 ms and 1.32 ms. SLA set
to be 10 ms. The SLA value is used as a reference, it has not been defined by
OPNFV.

TC005
-----
The IO read bandwidth actually refers to the storage throughput, which is
measured by fio and the greatest IO read bandwidth of the four runs is 175.4
MB/s. The IO read bandwidth of the four runs looks similar on different four
days, with an average between 58.1 and 62.0 MB/s, except one on Sep. 14, for
its maximum storage throughput is only 133.0 MB/s. One of the runs has a
minimum BW of 497 KM/s and other has a maximum BW of 177.4 MB/s. The SLA of read
bandwidth sets to be 400 MB/s, which is used as a reference, and it has not
been defined by OPNFV.

The results of storage IOPS for the five runs look similar with each other. The
IO read times per second of the five test runs have an average value between
1.20 K/s and 1.61 K/s, and meanwhile, the minimum result is only 41 times per
second.

TC010
-----
The tool we use to measure memory read latency is lmbench, which is a series of
micro benchmarks intended to measure basic operating system and hardware system
metrics. The memory read latency of the five runs is between 1.146 ns and 1.172
ns on average. The variations within each test run are quite different, some
vary from a large range and others have a small change. For example, the
largest change is on September 13, the memory read latency of which is ranging
from 1.152 ns to 1.221 ns. However, the results on September 14 change very
little. The SLA sets to be 30 ns. The SLA value is used as a reference, it has
not been defined by OPNFV.

TC011
-----
Iperf3 is a tool for evaluating the packet delay variation between 2 VMs on
different blades. The reported packet delay variations of the five test runs
differ from each other. In general, the packet delay of the first two runs look
similar, for they both stay stable within each run. And the mean packet delay of
of them are 0.07714 ms and 0.07982 ms respectively. Of the five runs, the third
has the worst result, because the packet delay reaches 0.08384 ms. The trend of
therest two runs look the same, for the average packet delay are 0.07808 ms and
0.07727 ms respectively. The SLA value sets to be 10 ms. The SLA value is used
as a reference, it has not been defined by OPNFV.

TC012
-----
Lmbench is also used to measure the memory read and write bandwidth, in which
we use bw_mem to obtain the results. Among the five test runs, the memory
bandwidth of last three test runs almost keep stable within each run, which is
11.64, 11.71 and 11.61 GB/s on average. However, the memory read and write
bandwidth on Sep. 13 has a large range, for it ranges from 6.68 GB/s to 11.73
GB/s. Here SLA set to be 15 GB/s. The SLA value is used as a reference, it has
not been defined by OPNFV.

TC014
-----
The Unixbench is used to evaluate the IaaS processing speed with regards to
score of single cpu running and parallel running. It can be seen from the
dashboard that the processing test results vary from scores 3208 to 3314, and
there is only one result one date. No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The mean packet throughput of the five test runs is between 259.6 kpps and
318.4 kpps, of which the result of the second run is the highest. The RTT
results of all the test runs keep flat at approx. 20 ms. It is obvious that the
PPS results are not as consistent as the RTT results.

The No. flows of the five test runs are 240 k on average and the PPS results
look a little waved since the largest packet throughput is 398.9 kpps and the
minimum throughput is 250.6 kpps respectively.

There are no errors of packets received in the five runs, but there are still
lost packets in all the test runs. The RTT values obtained by ping of the five
runs have the similar average vaue, that is between 17 ms and 22 ms, of which
the worest RTT is 53 ms on Sep. 14th.

CPU load is measured by mpstat, and CPU load of the four test runs seem a
little similar, since the minimum value and the peak of CPU load is between 0
percent and 10 percent respectively. And the best result is obtained on Sep.
13rd, with an CPU load of 10 percent.

TC069
-----
With the block size changing from 1 kb to 512 kb, the memory write bandwidth
tends to become larger first and then smaller within every run test, which
rangs from 21.6 GB/s to 26.8 GB/s and then to 18.4 GB/s on average. Since the
test id is one, it is that only the INT memory write bandwidth is tested. On
the whole, when the block size is 8 kb and 16 kb, the memory write bandwidth
look similar with a minimal BW of 23.0 GB/s and peak value of 28.6 GB/s. And
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

The network latency is measured by ping, and the results of the five test runs
look similar with each other, and within these test runs, the maximum RTT can
reach 53 ms and the average RTT is usually approx. 18 ms. The network latency
tested on Sep. 14 shows that it has a peak latency of 53 ms. But on the whole,
the average RTTs of the five runs keep flat and the network latency is
relatively short.

Memory utilization is measured by free, which can display amount of free and
used memory in the system. The largest amount of used memory is 272 MiB on Sep
14. In general, the mean used memory of the five test runs have the similar
trend and the minimum memory used size is approx. 150 MiB, and the average
used memory size is about 250 MiB. On the other hand, for the mean free memory,
the five test runs have the similar trend, whose mean free memory change from
218 MiB to 342 MiB, with an average value of approx. 38 MiB.

Packet throughput and packet loss can be measured by pktgen, which is a tool
in the network for generating traffic loads for network experiments. The mean
packet throughput of the five test runs seem quite different, ranging from
285.29 kpps to 297.76 kpps. The average number of flows in these tests is
240000, and each run has a minimum number of flows of 2 and a maximum number
of flows of 1.001 Mil. At the same time, the corresponding packet throughput
differ between 250.6k and 398.9k with an average packet throughput between
277.2 K and 318.4 K. In summary, the PPS results seem consistent. Within each
test run of the five runs, when number of flows becomes larger, the packet
throughput seems not larger at the same time.

TC071
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the five test runs
look similar with each other. Within each test run, the maximum RTT is only 49
ms and the average RTT is usually approx. 20 ms. On the whole, the average
RTTs of the five runs keep stable and the network latency is relatively short.

Cache utilization is measured by cachestat, which can display size of cache and
buffer in the system. Cache utilization statistics are collected during UDP
flows sent between the VMs using pktgen as packet generator tool.The largest
cache size is 215 MiB in the four runs, and the smallest cache size is 95 MiB.
On the whole, the average cache size of the five runs change a little and is
about 200 MiB, except the one on Sep. 14th, the mean cache size is very small,
which keeps 102 MiB. Meanwhile, the tread of the buffer size keep flat, since
they have a minimum value of 7 MiB and a maximum value of 8 MiB, with an
average value of about 7.8 MiB.

Packet throughput can be measured by pktgen, which is a tool in the network for
generating traffic loads for network experiments. The mean packet throughput of
the four test runs seem quite different, ranging from 285.29 kpps to 297.76
kpps. The average number of flows in these tests is 239.7k, and each run has a
minimum number of flows of 2 and a maximum number of flows of 1.001 Mil. At the
same time, the corresponding packet throughput differ between 227.3k and 398.9k
with an average packet throughput between 277.2k and 318.4k. Within each test
run of the five runs, when number of flows becomes larger, the packet
throughput seems not larger in the meantime.

TC072
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The RTT results are similar throughout the different test dates and runs
 between 0 ms and 49 ms with an average leatency of less than 22 ms. The PPS
results are not as consistent as the RTT results, for the mean packet
throughput of the five runs differ from 250.6 kpps to 398.9 kpps.

Network utilization is measured by sar, that is system activity reporter, which
can display the average statistics for the time since the system was started.
Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The largest total number of packets
transmitted per second look similar for four test runs, whose values change a
lot from 10 pps to 399 kpps, except the one on Sep. 14th, whose total number
of transmitted per second keep stable, that is 10 pps. Similarly, the total
number of packets received per second look the same for four runs, except the
one on Sep. 14th, whose value is only 10 pps.

In some test runs when running with less than approx. 90000 flows the PPS
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
