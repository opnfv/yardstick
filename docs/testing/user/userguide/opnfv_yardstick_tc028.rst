.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co., Ltd and others.

*************************************
Yardstick Test Case Description TC028
*************************************

.. _Cyclictest: https://rt.wiki.kernel.org/index.php/Cyclictest

+-----------------------------------------------------------------------------+
|KVM Latency measurements                                                     |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC028_KVM Latency measurements               |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | min, avg and max latency                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS KVM virtualization capability with      |
|              | regards to min, avg and max latency.                         |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs and similar shall be stored for comparison reasons    |
|              | and product evolution understanding between different OPNFV  |
|              | versions and/or configurations.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | file: samples/cyclictest-node-context.yaml                   |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | Cyclictest                                                   |
|              |                                                              |
|              | (Cyclictest is not always part of a Linux distribution,      |
|              | hence it needs to be installed. As an example see the        |
|              | /yardstick/tools/ directory for how to generate a Linux      |
|              | image with cyclictest included.)                             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | Cyclictest_                                                  |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | This test case is mainly for kvm4nfv project CI verify.      |
|              | Upgrade host linux kernel, boot a gust vm update it's linux  |
|              | kernel, and then run the cyclictest to test the new kernel   |
|              | is work well.                                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test kernel rpm, test sequence scripts and test guest    |
|conditions    | image need put the right folders as specified in the test    |
|              | case yaml file.                                              |
|              | The test guest image needs with cyclictest included in it.   |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The host and guest os kernel is upgraded. Cyclictest is      |
|              | invoked and logs are produced and stored.                    |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
