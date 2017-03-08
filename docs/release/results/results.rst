.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0

Results listed by scenario
==========================

The following sections describe the yardstick results as evaluated for the
Colorado release scenario validation runs. Each section describes the
determined state of the specific scenario as deployed in the Colorado
release process.

Scenario Results
================

.. _Dashboard: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _Jenkins: https://build.opnfv.org/ci/view/yardstick/

The following documents contain results of Yardstick test cases executed on
OPNFV labs, triggered by OPNFV CI pipeline, documented per scenario.


.. toctree::
   :maxdepth: 1

   os-nosdn-nofeature-ha.rst
   os-nosdn-nofeature-noha.rst
   os-odl_l2-nofeature-ha.rst
   os-odl_l2-bgpvpn-ha.rst
   os-odl_l2-sfc-ha.rst
   os-nosdn-kvm-ha.rst
   os-onos-nofeature-ha.rst
   os-onos-sfc-ha.rst

Test results of executed tests are avilable in Dashboard_ and logs in Jenkins_.


Feature Test Results
====================

The following features were verified by Yardstick test cases:

   * IPv6

   * HA (see :doc:`yardstick-opnfv-ha`)

   * KVM

   * Parser

   * Virtual Traffic Classifier (see :doc:`yardstick-opnfv-vtc`)

   * StorPerf

.. note:: The test cases for IPv6 and Parser Projects are included in the
  compass scenario.

