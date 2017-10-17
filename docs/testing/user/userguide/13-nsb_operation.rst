.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2016-2017 Intel Corporation.

Yardstick - NSB Testing - Operation
===================================

Abstract
--------

Advanced operations.

System Topology:
----------------

.. code-block:: console

  +----------+              +----------+
  |          |              |          |
  |          | (0)----->(0) |          |
  |    TG1   |              |    DUT   |
  |          |              |          |
  |          | (1)<-----(1) |          |
  +----------+              +----------+
  trafficgen_1                   vnf


Network Service Benchmarking - Bare-Metal
-----------------------------------------

Bare-Metal Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bare-Metal 2-Node setup:
^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

  +----------+              +----------+
  |          |              |          |
  |          | (0)----->(0) |          |
  |    TG1   |              |    DUT   |
  |          |              |          |
  |          | (n)<-----(n) |          |
  +----------+              +----------+
  trafficgen_1                   vnf

Bare-Metal 3-Node setup - Correlated Traffic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: console

  +----------+              +----------+              +------------+
  |          |              |          |              |            |
  |          |              |          |              |            |
  |          | (0)----->(0) |          |              |    UDP     |
  |    TG1   |              |    DUT   |              |   Replay   |
  |          |              |          |              |            |
  |          |              |          | (1)<---->(0) |            |
  +----------+              +----------+              +------------+
  trafficgen_1                   vnf                 trafficgen_2

Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.::

    cp /etc/yardstick/nodes/pod.yaml.nsb.sample /etc/yardstick/nodes/pod.yaml



Network Service Benchmarking - Standalone Virtualization
--------------------------------------------------------

SR-IOV:
^^^^^^^


SR-IOV Config pod.yaml describing Topology
##########################################

SR-IOV 2-Node setup:
####################
.. code-block:: console

                               +--------------------+
                               |                    |
                               |                    |
                               |        DUT         |
                               |       (VNF)        |
                               |                    |
                               +--------------------+
                               | VF NIC |  | VF NIC |
                               +--------+  +--------+
                                    ^          ^
                                    |          |
                                    |          |
                               +--------+  +--------+
                               - PF NIC -  - PF NIC -
  +----------+               +-------------------------+
  |          |               |       ^          ^      |
  |          |               |       |          |      |
  |          | (0)<----->(0) | ------           |      |
  |    TG1   |               |           SUT    |      |
  |          |               |                  |      |
  |          | (n)<----->(n) |------------------       |
  +----------+               +-------------------------+
  trafficgen_1                          host


SR-IOV 3-Node setup - Correlated Traffic
########################################
.. code-block:: console

                               +--------------------+
                               |                    |
                               |                    |
                               |        DUT         |
                               |       (VNF)        |
                               |                    |
                               +--------------------+
                               | VF NIC |  | VF NIC |
                               +--------+  +--------+
                                    ^          ^
                                    |          |
                                    |          |
                               +--------+  +--------+
                               | PF NIC -  - PF NIC -
  +----------+               +-------------------------+            +--------------+
  |          |               |       ^          ^      |            |              |
  |          |               |       |          |      |            |              |
  |          | (0)<----->(0) | ------           |      |            |     TG2      |
  |    TG1   |               |           SUT    |      |            | (UDP Replay) |
  |          |               |                  |      |            |              |
  |          | (n)<----->(n) |                  ------ | (n)<-->(n) |              |
  +----------+               +-------------------------+            +--------------+
  trafficgen_1                          host                       trafficgen_2

Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.

::

    cp /etc/yardstick/nodes/pod.yaml.nsb.sriov.sample /etc/yardstick/nodes/pod.yaml



OVS-DPDK:
^^^^^^^^^


OVS-DPDK Config pod.yaml describing Topology
############################################

OVS-DPDK 2-Node setup:
######################
.. code-block:: console

                               +--------------------+
                               |                    |
                               |                    |
                               |        DUT         |
                               |       (VNF)        |
                               |                    |
                               +--------------------+
                               | virtio |  | virtio |
                               +--------+  +--------+
                                    ^          ^
                                    |          |
                                    |          |
                               +--------+  +--------+
                               | vHOST0 |  | vHOST1 |
  +----------+               +-------------------------+
  |          |               |       ^          ^      |
  |          |               |       |          |      |
  |          | (0)<----->(0) | ------           |      |
  |    TG1   |               |          SUT     |      |
  |          |               |       (ovs-dpdk) |      |
  |          | (n)<----->(n) |------------------       |
  +----------+               +-------------------------+
  trafficgen_1                          host


OVS-DPDK 3-Node setup - Correlated Traffic
##########################################
.. code-block:: console

                               +--------------------+
                               |                    |
                               |                    |
                               |        DUT         |
                               |       (VNF)        |
                               |                    |
                               +--------------------+
                               | virtio |  | virtio |
                               +--------+  +--------+
                                    ^          ^
                                    |          |
                                    |          |
                               +--------+  +--------+
                               | vHOST0 |  | vHOST1 |
  +----------+               +-------------------------+            +--------------+
  |          |               |       ^          ^      |            |              |
  |          |               |       |          |      |            |              |
  |          | (0)<----->(0) | ------           |      |            |     TG2      |
  |    TG1   |               |          SUT     |      |            | (UDP Replay) |
  |          |               |      (ovs-dpdk)  |      |            |              |
  |          | (n)<----->(n) |                  ------ | (n)<-->(n) |              |
  +----------+               +-------------------------+            +--------------+
  trafficgen_1                          host                       trafficgen_2


Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.::

    cp /etc/yardstick/nodes/pod.yaml.nsb.ovs.sample /etc/yardstick/nodes/pod.yaml

