.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Ericsson AB and others.

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
|              | Average, minimum and maximun values are obtained.            |
|              | The purpose is also to be able to spot trends.               |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: cpuload.yaml (in the 'samples' directory)              |
|              |                                                              |
|              | * interval: 1 - repeat, pausing every 1 seconds in-between.  |
|              | * count: 10 - display statistics 10 times, then exit.        |
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
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              |  * interval;                                                 |
|              |  * count;                                                    |
|              |  * runner Iteration and intervals.                           |
|              |                                                              |
|              | There are default values for each above-mentioned option.    |
|              | Run in background with other test cases.                     |
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
