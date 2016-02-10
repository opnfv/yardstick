.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC014
*************************************

.. _unixbench: https://github.com/kdlucas/byte-unixbench/blob/master/UnixBench

+-----------------------------------------------------------------------------+
|Processing speed                                                             |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC014_Processing speed                       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | score of single cpu running, score of parallel running       |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS processing speed with regards to score  |
|              | of single cpu running and parallel running                   |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs and similar shall be stored for comparison reasons    |
|              | and product evolution understanding between different OPNFV  |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc014.yaml                             |
|              |                                                              |
|              | run_mode: Run unixbench in quiet mode or verbose mode        |
|              | test_type: dhry2reg, whetstone and so on                     |
|              |                                                              |
|              | For SLA with single_score and parallel_score, both can be    |
|              | set by user, default is NA                                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | unixbench                                                    |
|              |                                                              |
|              | (unixbench is not always part of a Linux distribution, hence |
|              | it needs to be installed. As an example see the              |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with unixbench included.)                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | unixbench_                                                   |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different test types, dhry2reg,  |
|              | whetstone and so on.                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with unixbench included in it.                               |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed, as a client. unixbench  is          |
|              | invoked and logs are produced and stored.                    |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
