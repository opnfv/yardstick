.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Huawei Technologies Co.,Ltd and others.

*************************************
Yardstick Test Case Description TC011
*************************************

.. _iperf3: https://iperf.fr/

+-----------------------------------------------------------------------------+
|Packet delay variation between VMs                                           |
|                                                                             |
+--------------+--------------------------------------------------------------+
|test case id  | OPNFV_YARDSTICK_TC011_Packet delay variation between VMs     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | jitter: packet delay variation (ms)                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | Measure the packet delay variation sending the packets from  |
|              | one VM to the other.                                         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|configuration | File: opnfv_yardstick_tc011.yaml                             |
|              |                                                              |
|              | * options:                                                   |
|              |   protocol: udp # The protocol used by iperf3 tools          |
|              |   bandwidth: 20m # It will send the given number of packets  |
|              |                    without pausing                           |
|              | * runner:                                                    |
|              |   duration: 30 # Total test duration 30 seconds.             |
|              |                                                              |
|              | * SLA (optional):                                            |
|              |   jitter: 10 (ms) # The maximum amount of jitter that is     |
|              |     accepted.                                                |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test tool     | iperf3                                                       |
|              |                                                              |
|              | iPerf3 is a tool for active measurements of the maximum      |
|              | achievable bandwidth on IP networks. It supports tuning of   |
|              | various parameters related to timing, buffers and protocols. |
|              | The UDP protocols can be used to measure jitter delay.       |
|              |                                                              |
|              | (iperf3 is not always part of a Linux distribution, hence it |
|              | needs to be installed. It is part of the Yardstick Docker    |
|              | image.                                                       |
|              | As an example see the /yardstick/tools/ directory for how    |
|              | to generate a Linux image with pktgen included.)             |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | iperf3_                                                      |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different:                       |
|              |                                                              |
|              | * bandwidth: Test case can be configured with different      |
|              |              bandwidth.                                      |
|              |                                                              |
|              | * duration: The test duration can be configured.             |
|              |                                                              |
|              | * jitter: SLA is optional. The SLA in this test case         |
|              |           serves as an example.                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with iperf3 included in the image.                           |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test sequence | description and expected result                              |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 1        | The hosts are installed, as server and client. iperf3 is     |
|              | invoked and logs are produced and stored.                    |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test should not PASS if any jitter is above the optional SLA |
|              | value, or if there is a test case execution problem.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
