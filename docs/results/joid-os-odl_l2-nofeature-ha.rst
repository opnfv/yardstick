.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


============================================
Test Results for joid-os-odl_l2-nofeature-ha
============================================

.. toctree::
   :maxdepth: 2


Details
=======

.. _Dashboard: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _POD2: https://wiki.opnfv.org/pharos_rls_b_labs


Overview of test results
------------------------

See Dashboard_ for viewing test result metrics for each respective test case.

All of the test case results below are based on scenario test runs on the
Orange POD2, between February 23 and February 24.

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

Not executed, missing in the test suite used in the POD during the observed
period.

TC011
-----

Not executed, missing in the test suite used in the POD during the observed
period.


TC012
-----

Not executed, missing in the test suite used in the POD during the observed
period.


TC014
-----

Not executed, missing in the test suite used in the POD during the observed
period.


TC037
-----

See Dashboard_ for results.


Detailed test results
---------------------

The scenario was run on Orange POD2_ with:
Joid
ODL Beryllium

Rationale for decisions
-----------------------

Pass

Most tests were successfully executed and metrics collected, the non-execution
of above-mentioned tests was due to test cases missing in the Jenkins Job used
in the POD, during the observed period.
No SLA was verified. To be decided on in next release of OPNFV.

Conclusions and recommendations
-------------------------------

Execute tests over a longer period of time, with time reference to versions of
components, for allowing better understanding of the behavior of the system.
