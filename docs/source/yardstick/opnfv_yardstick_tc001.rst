.. image:: ../../etc/opnfv-logo.png
  :height: 40
  :width: 200
  :alt: OPNFV
  :align: left

*************************************
Yardstick Test Case Description TC001
*************************************
+-----------------------------------------------------------------------------+
|Network Performance                                                          |
+==============+==============================================================+
|test case id  | OPNFV_YARDSTICK_TC001_NW PERF                                |
+--------------+--------------------------------------------------------------+
|metric        | Number of flows and throughput                               |
+--------------+--------------------------------------------------------------+
|test purpose  | To evaluate the IaaS network performance with regards to     |
|              | flows and throughput, such as if and how different amounts   |
|              | of flows matter for the throughput between hosts on different|
|              | compute blades. Typically e.g. the performance of a vSwitch  |
|              | depends on the number of flows running through it. Also      |
|              | performance of other equipment or entities can depend        |
|              | on the number of flows or the packet sizes used.             |
|              | The purpose is also to be able to spot trends. Test results, |
|              | graphs ans similar shall be stored for comparison reasons and|
|              | product evolution understanding between different OPNFV      |
|              | versions and/or configurations.                              |
+--------------+--------------------------------------------------------------+
|configuration | file: opnfv_yardstick_tc001.yaml                             |
|              |                                                              |
|              | - Packet size 64 bytes.                                      |
|              | - Number of ports set to 1, 10, 50, 100, 500 and 1000, where |
|              |   each amount runs for 20 seconds. The whole sequence is run |
|              |   twice. The amount of configured ports map to between 2 up  |
|              |   to 1001000 flows, respectively.                            |
|              | - Distribution policy for client and server to run on        |
|              |   different HW.                                              |
|              | - SLA max_ppm set to 1000.                                   |
+--------------+--------------------------------------------------------------+
|test tool     | pktgen                                                       |
|              |                                                              |
|              | (Pktgen is not always part of a Linux distribution, hence it |
|              | needs to be installed. It is part of the Yardstick Docker    |
|              | image.                                                       |
|              | As an example see the /yardstick/tools/ directory for how    |
|              | to generate a Linux image with pktgen included.)             |
+--------------+--------------------------------------------------------------+
|references    |https://www.kernel.org/doc/Documentation/networking/pktgen.txt|
|              |                                                              |
|              |ETSI-NFV-TST001                                               |
+--------------+--------------------------------------------------------------+
|applicability | Test can be configured with different packet sizes, amount   |
|              | of flows, VM distribution policy, test duration and SLA      |
|              | (optional). Default values exist.                            |
|              |                                                              |
|              | SLA: max_ppm is the number of packets per million packets    |
|              | packets sent acceptable to lose.                             |
+--------------+--------------------------------------------------------------+
|pre-test      | The test case image needs to be installed into Glance        |
|conditions    | with pktgen included in it.                                  |
|              |                                                              |
|              | No POD specific requirements have been identified.           |
+--------------+------+----------------------------------+--------------------+
|test sequence | step | description                      | result             |
|              +------+----------------------------------+--------------------+
|              |  1   | The hosts are installed, as      | Logs are stored    |
|              |      | server and client. pktgen is     |                    |
|              |      | invoked and logs are produced    |                    |
|              |      | and stored.                      |                    |
+--------------+------+----------------------------------+--------------------+
|test verdict  | Fails only if SLA is not passed, or if there is a test case  |
|              | execution problem.                                           |
+--------------+--------------------------------------------------------------+
