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
|test case id  | OPNFV_YARDSTICK_TC011_PACKET DELAY VARIATION BETWEEN VMs     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|metric        | jitter: packet delay variation (ms)                          |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test purpose  | The purpose of TC011 is to evaluate the IaaS network         |
|              | performance with regards to network jitter (packet delay     |
|              | variation).                                                  |
|              | It measures the packet delay variation sending the packets   |
|              | from one VM to the other.                                    |
|              |                                                              |
|              | The purpose is also to be able to spot the trends.           |
|              | Test results, graphs and similar shall be stored for         |
|              | comparison reasons and product evolution understanding       |
|              | between different OPNFV versions and/or configurations.      |
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
|              | image. As an example see the /yardstick/tools/ directory for |
|              | how to generate a Linux image with pktgen included.)         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test          | iperf3 test is invoked between a host VM and a target VM.    |
|description   |                                                              |
|              | Jitter calculations are continuously computed by the server, |
|              | as specified by RTP in RFC 1889. The client records a 64 bit |
|              | second/microsecond timestamp in the packet. The server       |
|              | computes the relative transit time as (server's receive time |
|              | - client's send time). The client's and server's clocks do   |
|              | not need to be synchronized; any difference is subtracted    |
|              | outin the jitter calculation. Jitter is the smoothed mean of |
|              | differences between consecutive transit times.               |
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
|usability     | This test case is one of Yardstick's generic test. Thus it   |
|              | is runnable on most of the scenarios.                        |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|references    | iperf3_                                                      |
|              |                                                              |
|              | ETSI-NFV-TST001                                              |
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
|step 1        | Two host VMs with iperf3 installed are booted, as server and |
|              | client.                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 2        | Yardstick is connected with the host VM by using ssh.        |
|              | A iperf3 server is started on the server VM via the ssh      |
|              | tunnel.                                                      |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 3        | iperf3 benchmark is invoked. Jitter is calculated and check  |
|              | against the SLA. Logs are produced and stored.               |
|              |                                                              |
|              | Result: Logs are stored.                                     |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|step 4        | The host VMs are deleted.                                    |
|              |                                                              |
+--------------+--------------------------------------------------------------+
|test verdict  | Test should not PASS if any jitter is above the optional SLA |
|              | value, or if there is a test case execution problem.         |
|              |                                                              |
+--------------+--------------------------------------------------------------+
