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

Results listed by test cases
----------------------------

.. _TOM: https://wiki.opnfv.org/display/testing/R+post-processing+of+the+Yardstick+results


The following sections describe the yardstick test case results as evaluated
for the OPNFV Fraser release scenario validation runs. Each section describes
the determined state of the specific test case as executed in the Fraser release
process. All test date are analyzed using TOM_ tool.

Scenario Results
----------------

.. _Dashboard: http://testresults.opnfv.org/grafana/dashboard/db/yardstick-main
.. _Jenkins: https://build.opnfv.org/ci/view/yardstick/


The following documents contain results of Yardstick test cases executed on
OPNFV labs, triggered by OPNFV CI pipeline, documented per test case.

For hardware details of OPNFV labs, please visit: https://wiki.opnfv.org/display/pharos/Community+Labs

.. toctree::
   :maxdepth: 1

   tc002-network-latency.rst
   tc010-memory-read-latency.rst
   tc011-packet-delay-variation.rst
   tc012-memory-read-write-bandwidth.rst
   tc014-cpu-processing-speed.rst
   tc069-memory-write-bandwidth.rst
   tc082-context-switches-under-load.rst
   tc083-network-throughput-between-vm.rst

Test results of executed tests are avilable in Dashboard_ and logs in Jenkins_.

Test results for Fraser release are collected from April 10, 2018 to May 13, 2018.

Feature Test Results
--------------------

The following features were verified by Yardstick test cases:

   * IPv6

   * HA (see :doc:`yardstick-opnfv-ha`)

   * KVM

   * Parser

   * StorPerf

.. note:: The test cases for IPv6 and Parser Projects are included in the
  compass scenario.

