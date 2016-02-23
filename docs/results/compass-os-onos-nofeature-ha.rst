.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


=============================================
Test Results for compass-os-onos-nofeature-ha
=============================================

.. toctree::
   :maxdepth: 2


Details
=======

.. _Dashboard: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _Sclara: https://wiki.opnfv.org/pharos_rls_b_labs


verview of test results
------------------------

See Dashboard_ for viewing test result metrics for each respective test case.

All of the test case results below are based on scenario test runs on the
Huawei Sclara_.

TC002
-----

See Dashboard_ for results.
SLA set to 10 ms, only used as a reference; no value has yet been defined by
OPNFV.

TC005
-----

See Dashboard_ for results.
SLA set to 400KB/s, only used as a reference; no value has yet been defined by
OPNFV.

TC010
-----

See Dashboard_ for results.
SLA set to 30ns, only used as a reference; no value has yet been defined by
OPNFV.

TC011
-----

See Dashboard_ for results.


TC012
-----

See Dashboard_ for results.
SLA set to 15 GB/s, only used as a reference; no value has yet been defined by
OPNFV.


TC014
-----

See Dashboard_ for results.
No SLA set.


TC037
-----

See Dashboard_ for results.


Detailed test results
---------------------

The scenario was run on Huawei Sclara_ POD with:
Compass
ONOS

Rationale for decisions
-----------------------

Pass

Tests were successfully executed and metrics collected.
No SLA was verified. To be decided on in next release of OPNFV.


Conclusions and recommendations
-------------------------------

Execute tests over a longer period of time, with time reference to versions of
components, for allowing better understanding of the behavior of the system.
