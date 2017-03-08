.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


==================================
Test Results for os-odl_l2-sfc-ha
==================================

.. toctree::
   :maxdepth: 2


Fuel
=====

.. _Grafana: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _POD2: https://wiki.opnfv.org/pharos?&#community_test_labs

Overview of test results
------------------------

See Grafana_ for viewing test result metrics for each respective test case. It
is possible to chose which specific scenarios to look at, and then to zoom in
on the details of each run test scenario as well.

All of the test case results below are based on 4 scenario test runs, each run
on the LF POD2_ or Ericsson POD2_ between September 16 and 20 in 2016.

TC002
-----
The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping. Most test run measurements result on average between 0.32 ms and 1.42 ms.
Only one test run on Sep. 20 has reached greatest RTT spike of 4.66 ms.
Meanwhile, the smallest network latency is 0.16 ms, which is obtained on Sep.
17th. To sum up, the curve of network latency has very small wave, which is
less than 5 ms. SLA sets to be 10 ms. The SLA value is used as a reference, it
has not been defined by OPNFV.

TC005
-----
The IO read bandwidth actually refers to the storage throughput, which is
measured by fio and the greatest IO read bandwidth of the four runs is 734
MB/s. The IO read bandwidth of the first three runs looks similar, with an
average of less than 100 KB/s, except one on Sep. 20, whose maximum storage
throughput can reach 734 MB/s. The SLA of read bandwidth sets to be 400 MB/s,
which is used as a reference, and it has not been defined by OPNFV.

The results of storage IOPS for the four runs look similar with each other. The
IO read times per second of the four test runs have an average value between
1.8k per second and 3.27k per second, and meanwhile, the minimum result is
only 60 times per second.

TC010
-----
The tool we use to measure memory read latency is lmbench, which is a series of
micro benchmarks intended to measure basic operating system and hardware system
metrics. The memory read latency of the four runs is between 1.085 ns and 1.218
ns on average. The variations within each test run are quite small. For
Ericsson pod2, the average of memory latency is approx. 1.217 ms. While for LF
pod2, the average value is about 1.085 ms. It can be seen that the performance
of LF is better than Ericsson's. The SLA sets to be 30 ns. The SLA value is
used as a reference, it has not been defined by OPNFV.

TC012
-----
Lmbench is also used to measure the memory read and write bandwidth, in which
we use bw_mem to obtain the results. The four test runs all have a narrow range
of change with the average memory and write BW of 18.5 GB/s. Here SLA set to be
15 GB/s. The SLA value is used as a reference, it has not been defined by OPNFV.

TC014
-----
The Unixbench is used to evaluate the IaaS processing speed with regards to
score of single cpu running and parallel running. It can be seen from the
dashboard that the processing test results vary from scores 3209k to 3843k, and
there is only one result one date. No SLA set.

TC037
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The mean packet throughput of the three test runs is between 439 kpps and
582 kpps, and the test run on Sep. 17th has the lowest average value of 371
kpps. The RTT results of all the test runs keep flat at approx. 10 ms. It is
obvious that the PPS results are not as consistent as the RTT results.

The No. flows of the four test runs are 240 k on average and the PPS results
look a little waved, since the largest packet throughput is 680 kpps and the
minimum throughput is 319 kpps respectively.

There are no errors of packets received in the four runs, but there are still
lost packets in all the test runs. The RTT values obtained by ping of the four
runs have the similar trend of RTT with the average value of approx. 12 ms.

CPU load is measured by mpstat, and CPU load of the four test runs seem a
little similar, since the minimum value and the peak of CPU load is between 0
percent and ten percent respectively. And the best result is obtained on Sep.
17th, with an CPU load of ten percent. But on the whole, the CPU load is very
poor, since the average value is quite small.

TC069
-----
With the block size changing from 1 kb to 512 kb, the average memory write
bandwidth tends to become larger first and then smaller within every run test
for the two pods, which rangs from 25.1 GB/s to 29.4 GB/s and then to 19.2 GB/s
on average. Since the test id is one, it is that only the INT memory write
bandwidth is tested. On the whole, with the block size becoming larger, the
memory write bandwidth tends to decrease. SLA sets to be 7 GB/s. The SLA value
is used as a reference, it has not been defined by OPNFV.

TC070
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other, and within these test runs, the maximum RTT can
reach 27 ms and the average RTT is usually approx. 12 ms. The network latency
tested on Sep. 27th has a peak latency of 27 ms. But on the whole, the average
RTTs of the four runs keep flat.

Memory utilization is measured by free, which can display amount of free and
used memory in the system. The largest amount of used memory is 269 MiB for the
four runs. In general, the four test runs have very large memory utilization,
which can reach 251 MiB on average. On the other hand, for the mean free memory,
the four test runs have the similar trend with that of the mean used memory.
In general, the mean free memory change from 231 MiB to 248 MiB.

Packet throughput and packet loss can be measured by pktgen, which is a tool
in the network for generating traffic loads for network experiments. The mean
packet throughput of the four test runs seem quite different, ranging from
371 kpps to 582 kpps. The average number of flows in these tests is
240000, and each run has a minimum number of flows of 2 and a maximum number
of flows of 1.001 Mil. At the same time, the corresponding average packet
throughput is between 319 kpps and 680 kpps. In summary, the PPS results
seem consistent. Within each test run of the four runs, when number of flows
becomes larger, the packet throughput seems not larger at the same time.

TC071
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The network latency is measured by ping, and the results of the four test runs
look similar with each other. Within each test run, the maximum RTT is only 24
ms and the average RTT is usually approx. 12 ms. On the whole, the average
RTTs of the four runs keep stable and the network latency is relatively small.

Cache utilization is measured by cachestat, which can display size of cache and
buffer in the system. Cache utilization statistics are collected during UDP
flows sent between the VMs using pktgen as packet generator tool. The largest
cache size is 213 MiB, and the smallest cache size is 99 MiB, which is same for
the four runs. On the whole, the average cache size of the four runs look the
same and is between 184 MiB and 205 MiB. Meanwhile, the tread of the buffer
size keep stable, since they have a minimum value of 7 MiB and a maximum value of
8 MiB.

Packet throughput can be measured by pktgen, which is a tool in the network for
generating traffic loads for network experiments. The mean packet throughput of
the four test runs differ from 371 kpps to 582 kpps. The average number of
flows in these tests is 240k, and each run has a minimum number of flows of 2
and a maximum number of flows of 1.001 Mil. At the same time, the corresponding
packet throughput differ between 319 kpps to 680 kpps. Within each test run
of the four runs, when number of flows becomes larger, the packet throughput
seems not larger in the meantime.

TC072
-----
The amount of packets per second (PPS) and round trip times (RTT) between 2 VMs
on different blades are measured when increasing the amount of UDP flows sent
between the VMs using pktgen as packet generator tool.

Round trip times and packet throughput between VMs can typically be affected by
the amount of flows set up and result in higher RTT and less PPS throughput.

The RTT results are similar throughout the different test dates and runs
between 0 ms and 24 ms with an average leatency of less than 13 ms. The PPS
results are not as consistent as the RTT results, for the mean packet
throughput of the four runs differ from 370 kpps to 582 kpps.

Network utilization is measured by sar, that is system activity reporter, which
can display the average statistics for the time since the system was started.
Network utilization statistics are collected during UDP flows sent between the
VMs using pktgen as packet generator tool. The largest total number of packets
transmitted per second look similar for the four test runs, whose values change a
lot from 10 pps to 697 kpps. However, the total number of packets received per
second of three runs look similar, which have a large wide range of 2 pps to
1.497 Mpps, while the results on Sep. 18th and 20th have very small maximum
number of packets received per second of 817 kpps.

In some test runs when running with less than approx. 251000 flows the PPS
throughput is normally flatter compared to when running with more flows, after
which the PPS throughput decreases. For the other test runs there is however no
significant change to the PPS throughput when the number of flows are
increased. In some test runs the PPS is also greater with 251000 flows
compared to other test runs where the PPS result is less with only 2 flows.

There are lost packets reported in most of the test runs. There is no observed
correlation between the amount of flows and the amount of lost packets.
The lost amount of packets normally differs a lot per test run.

Detailed test results
---------------------
The scenario was run on Ericsson POD2_ and LF POD2_ with:
Fuel 9.0
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
