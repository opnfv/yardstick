.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0


======================
Yardstick Test Results
======================

.. toctree::
   :maxdepth: 2


Scenario Results
================

.. _Dashboard: http://130.211.154.108/grafana/dashboard/db/yardstick-main
.. _Jenkins: https://build.opnfv.org/ci/view/yardstick/

The following documents contain results of Yardstick test cases executed on
OPNFV labs, triggered by OPNFV CI pipeline, documented per scenario.


Ready scenarios
---------------

The following scenarios run at least four consecutive times Yardstick test
cases suite:

.. toctree::
   :maxdepth: 1

   apex-os-odl_l2-nofeature-ha.rst
   compass-os-nosdn-nofeature-ha.rst
   compass-os-odl_l2-nofeature-ha.rst
   compass-os-onos-nofeature-ha.rst
   fuel-os-nosdn-nofeature-ha.rst
   fuel-os-odl_l2-nofeature-ha.rst
   fuel-os-onos-nofeature-ha.rst
   joid-os-odl_l2-nofeature-ha.rst
   yardstick-opnfv-vtc.rst


Limitations
-----------

The following scenarios run at least one time Yardstick test cases suite,
partially or complete:

   * fuel-os-odl_l2-sfc-ha

   * fuel-os-odl_l2-bgpvpn-ha

   * fuel-os-odl_l3-nofeature-ha

   * joid-os-nosdn-nofeature-ha


Test results of executed tests are avilable in Dashboard_ and logs in Jenkins_.


Not executed
------------

For the following scenarios, Yardstick test cases were not run:


   * apex-os-odl_l2-sfc-noha

   * apex-os-odl_l3-nofeature-ha

   * apex-os-onos-nofeature-ha

   * fuel-os-nosdn-kvm-ha

   * fuel-os-nosdn-ovs-ha

   * fuel-os-odl_l3-nofeature-ha

   * joid-os-onos-nofeature-ha

Logs are available in Jenkins_.


Feature Test Results
====================

The following features were verified by Yardstick test cases:

   * IPv6

   * HA (see :doc:`yardstick-opnfv-ha`)

   * KVM

   * Parser

.. note:: The test cases for IPv6 and Parser Projects are included in the
  compass scenario.
