*************************************
Yardstick Test Case Description TC024
*************************************

.. _man-pages: http://manpages.ubuntu.com/manpages/trusty/man1/mpstat.1.html

+-----------------------------------------------------------------------------+
| CPU Load                                                                    |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC024_CPU Load                               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | CPU load                                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the CPU load performance of the IaaS. This test  |
|              | case should be run in parallel to other Yardstick test cases |
|              | and not run as a stand-alone test case.                      |
|              |                                                              |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs ans similar shall be stored for comparison reasons and|
|              | product evolution understanding between different OPNFV      |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: cpuload.yaml (in the 'samples' directory)              |
|              |                                                              |
|              | There is are no additional configurations to be set for this |
|              | TC.                                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | mpstat                                                       |
|              |                                                              |
|              | (mpstat is not always part of a Linux distribution, hence it |
|              | needs to be installed. It is part of the Yardstick Glance    |
|              | image. However, if mpstat is not present the TC instead uses |
|              | /proc/stats as source to produce "mpstat" output.            |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | man-pages_                                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Run in background with other test cases.                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with mpstat included in it.                                  |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host is installed. The related TC, or TCs, is            |
|              | invoked and mpstat logs are produced and stored.             |
|              |                                                              |
|              | Result: Stored logs                                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | None. CPU load results are fetched and stored.               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
