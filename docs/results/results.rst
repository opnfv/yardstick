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


Ready scenarios
---------------

The following scenarios have been successfully tested at least four consecutive
times:

.. toctree::
   :maxdepth: 1

   fuel-os-odl_l2-nofeature-ha.rst
   fuel-os-odl_l3-nofeature-noha.rst
   fuel-os-nosdn-kvm-ha.rst
   fuel-os-nosdn-kvm-noha.rst
   fuel-os-odl_l2-bgpvpn-ha.rst
   fuel-os-odl_l2-bgpvpn-noha.rst
   compass-os-nosdn-nofeature-ha.rst
   compass-os-odl_l2-moon-ha.rst
   compass-os-onos-sfc-ha.rst
   compass-onos-nofeature-ha.rst
   joid-os-nosdn-nofeature-ha.rst
   joid-os-nosdn-nofeature-noha.rst
   joid-odl_l2-nofeature-ha.rst
   joid-os-onos-nofeature-ha.rst
   joid-os-onos-sfc-ha.rst
   apex-os-nosdn-nofeature-ha.rst
   apex-os-odl_l2-bgpvpn-ha.rst

Limitations
-----------

For the following scenarios, Yardstick generic test cases suite was executed at
least one time however less than four consecutive times, measurements
collected:


   * fuel-os-odl_l3-nofeature-ha


For the following scenario, Yardstick generic test cases suite was executed
four consecutive times, measurements collected; no feature test cases were
executed, therefore the feature is not verified by Yardstick:



For the following scenario, Yardstick generic test cases suite was executed
three consecutive times, measurements collected; no feature test cases
were executed, therefore the feature is not verified by Yardstick:

    * fuel-os-odl_l2-sfc-ha


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

