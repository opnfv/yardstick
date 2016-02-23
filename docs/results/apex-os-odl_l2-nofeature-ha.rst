.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


============================================
Test Results for apex-os-odl_l2-nofeature-ha
============================================

.. toctree::
   :maxdepth: 2


Details
=======

.. _Dashboard: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _POD1: https://wiki.opnfv.org/pharos_rls_b_labs

Overview of test results
------------------------

See Dashboard_ for viewing test result metrics for each respective test case.

All of the test case results below are based on scenario test runs on the
LF POD1, between February 19 and February 24.

TC002
-----

The round-trip-time (RTT) between 2 VMs on different blades is measured using
ping.

The results for the observed period show minimum 0.37ms, maximum 0.49ms,
average 0.45ms.
SLA set to 10 ms, only used as a reference; no value has yet been defined by
OPNFV.

TC005
-----

The IO read bandwidth for the observed period show average between 124KB/s and
129 KB/s, with a minimum 372KB/s and maximum 448KB/s.

SLA set to 400KB/s, only used as a reference; no value has yet been defined by
OPNFV.

TC010
-----

The measurements for memory latency for various sizes and strides are shown in
Dashboard_. For 48MB, the minimum is 22.75 and maximum 30.77 ns.

SLA set to 30 ns, only used as a reference; no value has yet been defined by
OPNFV.

TC011
-----

Packet delay variation between 2 VMs on different blades is measured using
Iperf3.

The mimimum packet delay variation measured is 2.5us and the maximum 8.6us.

TC012
-----

See Dashboard_ for results.

SLA set to 15 GB/s, only used as a reference, no value has yet been defined by
OPNFV.

TC014
-----

The Unixbench processor single and parallel speed scores show scores between
3625 and 3660.

No SLA set.

TC037
-----

See Dashboard_ for results.

Detailed test results
---------------------

The scenario was run on LF POD1_ with:
Apex
ODL Beryllium


Rationale for decisions
-----------------------

Pass

Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.

Conclusions and recommendations
-------------------------------

Execute tests over a longer period of time, with time reference to versions of
components, for allowing better understanding of the behavior of the system.
