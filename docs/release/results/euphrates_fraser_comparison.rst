.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0

..
      Convention for heading levels in Yardstick:
      =======  Heading 0 (reserved for the title in a document)
      -------  Heading 1
      ^^^^^^^  Heading 2
      +++++++  Heading 3
      '''''''  Heading 4
      Avoid deeper levels because they do not render well.

Test results analysis for Euphrates and Fraser releases
=======================================================

TC002
-----

The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping.

Most test run measurements result on average between 0.39 and 4.00 ms.
Compared with Euphrates release, the average RTT result of the same pod experiences
a slight decline in Fraser release. For example, the average RTT of arm-pod5 is
1.518 in Ehphrates and 1.714 in Fraser. The average RTT of intel-pod18 is 1.6575
ms in Ehphrates and 1.856 ms in Fraser.

{

    "huawei-pod2:stable/euphrates": [0.3925],

    "lf-pod2:stable/euphrates": [0.5315],

    "lf-pod1:stable/euphrates": [0.62],

    "huawei-pod2:stable/fraser": [0.677],

    "lf-pod1:stable/fraser": [0.725],

    "flex-pod2:stable/euphrates": [0.795],

    "huawei-pod12:stable/euphrates": [0.87],

    "ericsson-pod1:stable/fraser": [0.9165],

    "huawei-pod12:stable/fraser": [1.0465],

    "lf-pod2:stable/fraser": [1.2325],

    "intel-pod5:stable/euphrates": [1.25],

    "ericsson-virtual3:stable/euphrates": [1.2655],

    "ericsson-pod1:stable/euphrates": [1.372],

    "zte-pod2:stable/fraser": [1.395],

    "arm-pod5:stable/euphrates": [1.518],

    "huawei-virtual4:stable/euphrates": [1.5355],

    "ericsson-virtual4:stable/fraser": [1.582],

    "huawei-virtual3:stable/euphrates": [1.606],

    "intel-pod18:stable/euphrates": [1.6575],

    "huawei-virtual4:stable/fraser": [1.697],

    "huawei-virtual8:stable/euphrates": [1.709],

    "arm-pod5:stable/fraser": [1.714],

    "huawei-virtual3:stable/fraser": [1.716],

    "intel-pod18:stable/fraser": [1.856],

    "huawei-virtual2:stable/euphrates": [1.872],

    "arm-pod6:stable/euphrates": [1.895],

    "huawei-virtual2:stable/fraser": [1.964],

    "huawei-virtual1:stable/fraser": [1.9765],

    "huawei-virtual9:stable/euphrates": [2.0745],

    "arm-pod6:stable/fraser": [2.209],

    "huawei-virtual1:stable/euphrates": [2.495],

    "ericsson-virtual2:stable/euphrates": [2.7895],

    "ericsson-virtual4:stable/euphrates": [3.768],

    "ericsson-virtual1:stable/euphrates": [3.8035],

    "ericsson-virtual3:stable/fraser": [3.9175],

    "ericsson-virtual2:stable/fraser": [4.004]

}

TC010
-----

The tool we use to measure memory read latency is lmbench, which is a series of
micro benchmarks intended to measure basic operating system and hardware system
metrics. Compared with Euphrates release, the memory read latency of the same pod
also experience a slight decline. Virtual pods seem to have a higher memory read
latency than physical pods. Compared with X86 pods, the memory read latency of
arm pods is significant higher.

{

    "ericsson-pod1:stable/euphrates": [5.7785],

    "flex-pod2:stable/euphrates": [5.908],

    "ericsson-virtual1:stable/euphrates": [6.412],

    "intel-pod18:stable/euphrates": [6.5905],

    "intel-pod5:stable/euphrates": [6.6975],

    "ericsson-pod1:stable/fraser": [7.0645],

    "ericsson-virtual4:stable/euphrates": [7.183],

    "intel-pod18:stable/fraser": [7.4465],

    "zte-pod2:stable/fraser": [8.1865],

    "ericsson-virtual2:stable/euphrates": [8.4985],

    "huawei-pod2:stable/euphrates": [8.877],

    "huawei-pod12:stable/euphrates": [9.091],

    "huawei-pod2:stable/fraser": [9.236],

    "huawei-pod12:stable/fraser": [9.615],

    "ericsson-virtual3:stable/euphrates": [9.719],

    "ericsson-virtual2:stable/fraser": [9.8925],

    "huawei-virtual4:stable/euphrates": [10.1195],

    "huawei-virtual3:stable/euphrates": [10.19],

    "huawei-virtual2:stable/fraser": [10.22],

    "huawei-virtual1:stable/euphrates": [10.3045],

    "huawei-virtual9:stable/euphrates": [10.318],

    "ericsson-virtual4:stable/fraser": [10.5465],

    "ericsson-virtual3:stable/fraser": [10.9355],

    "huawei-virtual3:stable/fraser": [10.95],

    "huawei-virtual2:stable/euphrates": [11.274],

    "huawei-virtual4:stable/fraser": [11.557],

    "lf-pod1:stable/euphrates": [15.7025],

    "lf-pod2:stable/euphrates": [15.8495],

    "lf-pod2:stable/fraser": [16.5595],

    "lf-pod1:stable/fraser": [16.8395],

    "arm-pod5:stable/euphrates": [18.092],

    "arm-pod5:stable/fraser": [18.744],

    "huawei-virtual1:stable/fraser": [19.8235],

    "huawei-virtual8:stable/euphrates": [33.999],

    "arm-pod6:stable/euphrates": [41.5605],

    "arm-pod6:stable/fraser": [55.804]

}

TC011
-----

Iperf3 is a tool for evaluating the packet delay variation between 2 VMs on
different blades. In general, the packet delay variation of the two releases
look similar.

{

    "arm-pod6:stable/fraser": [1],

    "ericsson-pod1:stable/fraser": [1],

    "ericsson-virtual2:stable/fraser": [1],

    "ericsson-virtual3:stable/fraser": [1],

    "lf-pod2:stable/fraser": [1],

    "huawei-virtual1:stable/fraser": [2997],

    "huawei-virtual2:stable/euphrates": [2997],

    "flex-pod2:stable/euphrates": [2997.5],

    "huawei-virtual3:stable/euphrates": [2998],

    "huawei-virtual3:stable/fraser": [2999],

    "huawei-virtual9:stable/euphrates": [3000],

    "huawei-virtual8:stable/euphrates": [3001],

    "huawei-virtual4:stable/euphrates": [3002],

    "huawei-virtual4:stable/fraser": [3002],

    "ericsson-virtual3:stable/euphrates": [3006],

    "huawei-virtual1:stable/euphrates": [3007],

    "ericsson-virtual2:stable/euphrates": [3009],

    "intel-pod18:stable/euphrates": [3010],

    "ericsson-virtual4:stable/euphrates": [3017],

    "lf-pod2:stable/euphrates": [3021],

    "arm-pod5:stable/euphrates": [3022],

    "arm-pod6:stable/euphrates": [3022],

    "ericsson-pod1:stable/euphrates": [3022],

    "huawei-pod12:stable/euphrates": [3022],

    "huawei-pod12:stable/fraser": [3022],

    "huawei-pod2:stable/euphrates": [3022],

    "huawei-pod2:stable/fraser": [3022],

    "intel-pod18:stable/fraser": [3022],

    "intel-pod5:stable/euphrates": [3022],

    "lf-pod1:stable/euphrates": [3022],

    "lf-pod1:stable/fraser": [3022],

    "zte-pod2:stable/fraser": [3022],

    "huawei-virtual2:stable/fraser": [3025]

}

TC012
-----

Lmbench is also used to measure the memory read and write bandwidth.
Like TC010, compared with Euphrates release, the memory read and write bandwidth
of the same pod also experience a slight decline. And compared with X86 pods, the memory
read and write bandwidth of arm pods is significant lower.

{

    "lf-pod1:stable/euphrates": [22912.39],

    "lf-pod2:stable/euphrates": [22637.67],

    "lf-pod1:stable/fraser": [20552.9],

    "flex-pod2:stable/euphrates": [20229.99],

    "lf-pod2:stable/fraser": [20058.925],

    "ericsson-pod1:stable/fraser": [18930.78],

    "intel-pod18:stable/fraser": [18757.545],

    "ericsson-virtual1:stable/euphrates": [17474.965],

    "ericsson-pod1:stable/euphrates": [17127.38],

    "ericsson-virtual4:stable/euphrates": [16219.97],

    "ericsson-virtual2:stable/euphrates": [15652.28],

    "ericsson-virtual3:stable/euphrates": [15551.26],

    "ericsson-virtual4:stable/fraser": [15389.465],

    "ericsson-virtual2:stable/fraser": [15343.79],

    "huawei-pod2:stable/euphrates": [15017.2],

    "huawei-pod2:stable/fraser": [14870.78],

    "huawei-virtual4:stable/euphrates": [14266.34],

    "huawei-virtual1:stable/euphrates": [14233.035],

    "huawei-virtual3:stable/euphrates": [14227.63],

    "zte-pod2:stable/fraser": [14157.99],

    "huawei-pod12:stable/euphrates": [14147.245],

    "huawei-pod12:stable/fraser": [14126.99],

    "intel-pod18:stable/euphrates": [14058.33],

    "huawei-virtual3:stable/fraser": [13929.67],

    "huawei-virtual2:stable/euphrates": [13862.85],

    "huawei-virtual4:stable/fraser": [13847.155],

    "huawei-virtual2:stable/fraser": [13702.92],

    "huawei-virtual1:stable/fraser": [13496.45],

    "intel-pod5:stable/euphrates": [13280.32],

    "ericsson-virtual3:stable/fraser": [12733.19],

    "huawei-virtual9:stable/euphrates": [12559.445],

    "huawei-virtual8:stable/euphrates": [8998.02],

    "arm-pod5:stable/euphrates": [4388.875],

    "arm-pod5:stable/fraser": [4326.11],

    "arm-pod6:stable/euphrates": [4260.2],

    "arm-pod6:stable/fraser": [3809.885]

}

TC014
-----

The Unixbench is used to evaluate the IaaS processing speed with regards to
score of single CPU running and parallel running. Below are the single CPU running
scores. It can be seen that the processing test results vary from scores 715 to 3737.
In general, the single CPU score of the two releases look similar.

{

    "lf-pod2:stable/fraser": [3737.6],

    "lf-pod2:stable/euphrates": [3723.95],

    "lf-pod1:stable/fraser": [3702.7],

    "lf-pod1:stable/euphrates": [3669],

    "intel-pod5:stable/euphrates": [3388.6],

    "intel-pod18:stable/euphrates": [3298.4],

    "flex-pod2:stable/euphrates": [3208.6],

    "ericsson-pod1:stable/fraser": [3131.6],

    "intel-pod18:stable/fraser": [3098.1],

    "ericsson-virtual1:stable/euphrates": [2988.9],

    "zte-pod2:stable/fraser": [2831.4],

    "ericsson-pod1:stable/euphrates": [2669.1],

    "ericsson-virtual4:stable/euphrates": [2598.5],

    "ericsson-virtual2:stable/fraser": [2559.7],

    "ericsson-virtual3:stable/euphrates": [2553.15],

    "huawei-pod2:stable/euphrates": [2531.2],

    "huawei-pod2:stable/fraser": [2528.9],

    "ericsson-virtual4:stable/fraser": [2527.8],

    "ericsson-virtual2:stable/euphrates": [2526.9],

    "huawei-virtual4:stable/euphrates": [2407.4],

    "huawei-virtual3:stable/fraser": [2379.1],

    "huawei-virtual3:stable/euphrates": [2374.6],

    "huawei-virtual4:stable/fraser": [2362.1],

    "huawei-virtual2:stable/euphrates": [2326.4],

    "huawei-virtual9:stable/euphrates": [2324.95],

    "huawei-virtual1:stable/euphrates": [2302.6],

    "huawei-virtual2:stable/fraser": [2299.3],

    "huawei-pod12:stable/euphrates": [2232.2],

    "huawei-pod12:stable/fraser": [2229],

    "huawei-virtual1:stable/fraser": [2171.3],

    "ericsson-virtual3:stable/fraser": [2104.8],

    "huawei-virtual8:stable/euphrates": [2085.3],

    "arm-pod5:stable/fraser": [1764.2],

    "arm-pod5:stable/euphrates": [1754.4],

    "arm-pod6:stable/euphrates": [716.15],

    "arm-pod6:stable/fraser": [715.4]

}

TC069
-----

With the block size changing from 1 kb to 512 kb, the memory write bandwidth
tends to become larger first and then smaller within every run test. Below are
the scores for 32mb block array.

{

    "intel-pod18:stable/euphrates": [18871.79],

    "intel-pod18:stable/fraser": [16939.24],

    "intel-pod5:stable/euphrates": [16055.79],

    "arm-pod6:stable/euphrates": [13327.02],

    "arm-pod6:stable/fraser": [11895.71],

    "flex-pod2:stable/euphrates": [9384.585],

    "zte-pod2:stable/fraser": [9375.33],

    "ericsson-pod1:stable/euphrates": [9331.535],

    "huawei-pod12:stable/euphrates": [9164.88],

    "ericsson-pod1:stable/fraser": [9140.42],

    "huawei-pod2:stable/euphrates": [9026.52],

    "huawei-pod12:stable/fraser": [8993.37],

    "huawei-virtual9:stable/euphrates": [8825.805],

    "huawei-pod2:stable/fraser": [8794.01],

    "huawei-virtual2:stable/fraser": [7670.21],

    "ericsson-virtual1:stable/euphrates": [7615.97],

    "ericsson-virtual4:stable/euphrates": [7539.23],

    "arm-pod5:stable/fraser": [7479.32],

    "arm-pod5:stable/euphrates": [7403.38],

    "huawei-virtual3:stable/euphrates": [7247.89],

    "ericsson-virtual2:stable/fraser": [7219.21],

    "huawei-virtual2:stable/euphrates": [7205.35],

    "huawei-virtual1:stable/euphrates": [7196.405],

    "ericsson-virtual3:stable/euphrates": [7173.72],

    "huawei-virtual4:stable/euphrates": [7131.47],

    "ericsson-virtual2:stable/euphrates": [7129.08],

    "huawei-virtual4:stable/fraser": [7059.045],

    "huawei-virtual3:stable/fraser": [7023.57],

    "lf-pod1:stable/euphrates": [6928.18],

    "lf-pod2:stable/euphrates": [6875.88],

    "lf-pod2:stable/fraser": [6834.7],

    "lf-pod1:stable/fraser": [6775.27],

    "ericsson-virtual4:stable/fraser": [6522.86],

    "ericsson-virtual3:stable/fraser": [5835.59],

    "huawei-virtual8:stable/euphrates": [5729.705],

    "huawei-virtual1:stable/fraser": [5617.12]

}

TC082
-----

For this test case, we use perf to measure context-switches under load.
High context switch rates are not themselves an issue, but they may point the
way to a more significant problem.

{

    "zte-pod2:stable/fraser": [306.5],

    "huawei-pod12:stable/euphrates": [316],

    "lf-pod2:stable/fraser": [337.5],

    "intel-pod18:stable/euphrates": [340],

    "intel-pod18:stable/fraser": [343.5],

    "intel-pod5:stable/euphrates": [357.5],

    "ericsson-pod1:stable/euphrates": [384],

    "lf-pod2:stable/euphrates": [394.5],

    "huawei-pod12:stable/fraser": [399],

    "lf-pod1:stable/euphrates": [435],

    "lf-pod1:stable/fraser": [454],

    "flex-pod2:stable/euphrates": [476],

    "huawei-pod2:stable/euphrates": [518],

    "huawei-pod2:stable/fraser": [544.5],

    "arm-pod5:stable/euphrates": [869.5],

    "huawei-virtual9:stable/euphrates": [1002],

    "huawei-virtual4:stable/fraser": [1138],

    "huawei-virtual4:stable/euphrates": [1174],

    "huawei-virtual3:stable/euphrates": [1239],

    "ericsson-pod1:stable/fraser": [1305],

    "huawei-virtual2:stable/euphrates": [1430],

    "huawei-virtual3:stable/fraser": [1433],

    "huawei-virtual1:stable/fraser": [1470],

    "huawei-virtual1:stable/euphrates": [1489],

    "arm-pod6:stable/fraser": [1738.5],

    "arm-pod6:stable/euphrates": [1883.5]

}

TC083
-----

TC083 measures network latency and throughput between VMs using netperf.
The test results shown below are for UDP throughout.

{

    "lf-pod1:stable/euphrates": [2204.42],

    "lf-pod2:stable/fraser": [1893.39],

    "intel-pod18:stable/euphrates": [1835.55],

    "lf-pod2:stable/euphrates": [1676.705],

    "intel-pod5:stable/euphrates": [1612.555],

    "zte-pod2:stable/fraser": [1543.995],

    "lf-pod1:stable/fraser": [1480.86],

    "intel-pod18:stable/fraser": [1417.015],

    "flex-pod2:stable/euphrates": [1370.23],

    "huawei-pod12:stable/euphrates": [1300.12]

}
