.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2016-2017 Intel Corporation.

.. Convention for heading levels in Yardstick documentation:

   =======  Heading 0 (reserved for the title in a document)
   -------  Heading 1
   ^^^^^^^  Heading 2
   +++++++  Heading 3
   '''''''  Heading 4

   Avoid deeper levels because they do not render well.

===================================
Network Services Benchmarking (NSB)
===================================

.. _Yardstick: https://wiki.opnfv.org/yardstick
.. _`ETSI GS NFV-TST001`: http://www.etsi.org/deliver/etsi_gs/NFV-TST/001_099/001/01.01.01_60/gs_nfv-tst001v010101p.pdf

Abstract
--------

This chapter provides an overview of the NSB, a contribution to OPNFV
Yardstick_ from Intel.

Overview
--------

Network Services Benchmarking (:term:`NSB`) uses the :term:`Yardstick`
framework for performing :term:`VNF` and :term:`NFVI` characterisation in an
:term:`NFV` environment.

For VNF characterisation, NSB will onboard a VNF, source and sink traffic to it
via traffic generators, and collect a variety of key performance indicators
(:term:`KPI`) during VNF execution. The stream of KPI data is stored in a
database, and it is visualized in a performance-visualization dashboard.

For NFVI characterisation, a fixed test VNF, called :term:`PROX` is used.
PROX implements a suite of test cases and visualizes the output data of the
test suite. The PROX test cases implement various execution kernels found in
real-world VNFs, and the output of the test cases provides an indication of
the fitness of the infrastructure for running NFV services, in addition to
indicating potential performance optimizations for the NFVI.

NSB extends the Yardstick framework to do VNF characterization in three
different execution environments - bare metal i.e. native Linux environment,
standalone virtual environment and managed virtualized environment (e.g.
OpenStack). It also brings in the capability to interact with external traffic
generators, both hardware and software based, for triggering and validating the
traffic according to user defined profiles.

NSB extension includes:

* Generic data models of Network Services, based on ETSI spec
  `ETSI GS NFV-TST 001`_
* Standalone :term:`context` for VNF testing with SRIOV, OVS, OVS-DPDK, etc
* Generic VNF configuration models and metrics implemented with Python
  classes
* Traffic generator features and traffic profiles

    * L1-L3 stateless traffic profiles
    * L4-L7 state-full traffic profiles
    * Tunneling protocol/network overlay support

* Test case samples

    * Ping
    * Trex
    * vPE, vCGNAT, vFirewall etc - ipv4 throughput, latency etc

* Traffic generators i.e. Trex, ab/nginx, ixia, iperf, etc
* KPIs for a given use case:

    * System agent support for collecting NFVi KPI. This includes:

        * CPU statistic
        * Memory BW
        * OVS-DPDK Stats

    * Network KPIs e.g. inpackets, outpackets, thoughput, latency
    * VNF KPIs e.g. packet_in, packet_drop, packet_fwd

Architecture
------------

The Network Service (NS) defines a set of Virtual Network Functions (VNF)
connected together using NFV infrastructure.

The Yardstick NSB extension can support multiple VNFs created by different
vendors including traffic generators. Every VNF being tested has its
own data model. The Network service defines a VNF modelling on base of
performed network functionality. The part of the data model is a set of the
configuration parameters, number of connection points used and flavor including
core and memory amount.

ETSI defines a Network Service as a set of configurable VNFs working in some
NFV Infrastructure connecting each other using Virtual Links available through
Connection Points. The ETSI MANO specification defines a set of management
entities called Network Service Descriptors (NSD) and VNF Descriptors (VNFD)
that define real Network Service. The picture below makes an example how the
real Network Operator use-case can map into ETSI Network service definition.

Network Service framework performs the necessary test steps. It may involve:

* Interacting with traffic generator and providing the inputs on traffic
  type / packet structure to generate the required traffic as per the
  test case. Traffic profiles will be used for this.
* Executing the commands required for the test procedure and analyses the
  command output for confirming whether the command got executed correctly
  or not e.g. as per the test case, run the traffic for the given
  time period and wait for the necessary time delay.
* Verify the test result.
* Validate the traffic flow from SUT.
* Fetch the data from SUT and verify the value as per the test case.
* Upload the logs from SUT onto the Test Harness server
* Retrieve the KPI's provided by particular VNF

Components of Network Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Models for Network Service benchmarking*: The Network Service benchmarking
  requires the proper modelling approach. The NSB provides models using Python
  files and defining of NSDs and VNFDs.

The benchmark control application being a part of OPNFV Yardstick can call
that Python models to instantiate and configure the VNFs. Depending on
infrastructure type (bare-metal or fully virtualized) that calls could be
made directly or using MANO system.

* *Traffic generators in NSB*: Any benchmark application requires a set of
  traffic generator and traffic profiles defining the method in which traffic
  is generated.

The Network Service benchmarking model extends the Network Service
definition with a set of Traffic Generators (TG) that are treated
same way as other VNFs being a part of benchmarked network service.
Same as other VNFs the traffic generator are instantiated and terminated.

Every traffic generator has own configuration defined as a traffic profile
and a set of KPIs supported. The python models for TG is extended by
specific calls to listen and generate traffic.

* *The stateless TREX traffic generator*: The main traffic generator used as
  Network Service stimulus is open source TREX tool.

The TREX tool can generate any kind of stateless traffic.

.. code-block:: console

        +--------+      +-------+      +--------+
        |        |      |       |      |        |
        |  Trex  | ---> |  VNF  | ---> |  Trex  |
        |        |      |       |      |        |
        +--------+      +-------+      +--------+

Supported testcases scenarios:

* Correlated UDP traffic using TREX traffic generator and replay VNF.

    * using different IMIX configuration like pure voice, pure video traffic etc
    * using different number IP flows e.g. 1, 1K, 16K, 64K, 256K, 1M flows
    * Using different number of rules configured e.g. 1, 1K, 10K rules

For UDP correlated traffic following Key Performance Indicators are collected
for every combination of test case parameters:

* RFC2544 throughput for various loss rate defined (1% is a default)

Graphical Overview
------------------

NSB Testing with Yardstick framework facilitate performance testing of various
VNFs provided.

.. code-block:: console

  +-----------+
  |           |                                             +-------------+
  |   vPE     |                                          -->| TGen Port 0 |
  | TestCase  |                                          |  +-------------+
  |           |                                          |
  +-----------+     +---------------+      +-------+     |
                    |               | ---> |  VNF  | <--->
  +-----------+     |   Yardstick   |      +-------+     |
  | Test Case | --> |  NSB Testing  |                    |
  +-----------+     |               |                    |
        |           |               |                    |
        |           +---------------+                    |
  +-----------+                                          |  +-------------+
  |   Traffic |                                          -->| TGen Port 1 |
  |  patterns |                                             +-------------+
  +-----------+

              Figure 1: Network Service - 2 server configuration

VNFs supported for chracterization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. CGNAPT - Carrier Grade Network Address and port Translation
2. vFW - Virtual Firewall
3. vACL - Access Control List
4. PROX - Packet pROcessing eXecution engine:
     * VNF can act as Drop, Basic Forwarding (no touch),
       L2 Forwarding (change MAC), GRE encap/decap, Load balance based on
       packet fields, Symmetric load balancing
     * QinQ encap/decap IPv4/IPv6, ARP, QoS, Routing, Unmpls, Policing, ACL
5. UDP_Replay
