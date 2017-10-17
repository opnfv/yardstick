.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2016-2017 Intel Corporation.

Yardstick - NSB Testing - Operation
===================================

Abstract
--------

NSB test configuration and OpenStack setup requirments


OpenStack Network Configuration
-------------------------------

NSB requires certain OpenStack deployment configurations.
For optimal VNF characterization using external traffic generators NSB requires
provider/external networks.


Provider networks
^^^^^^^^^^^^^^^^^

The VNFs require a clear L2 connect to the external network in order to generate
realistic traffic from multiple address ranges and port

In order to prevent Neutron from filtering traffic we have to disable Neutron Port Security.
We also disable DHCP on the data ports because we are binding the ports to DPDK and do not need
DHCP addresses.  We also disable gateways because mutiple default gateways can prevent SSH access
to the VNF from the floating IP.  We only want a gateway on the mgmt network

.. code-block:: yaml

    uplink_0:
      cidr: '10.1.0.0/24'
      gateway_ip: 'null'
      port_security_enabled: False
      enable_dhcp: 'false'

Heat Topologies
^^^^^^^^^^^^^^^

By default Heat will attach every node to every Neutron network that is created.
For scale-out tests we do not want to attach every node to every network.

For each node you can specify which ports are on which network using the
network_ports dictionary.

In this example we have TRex xe0 <-> xe0 VNF xe1 <-> xe0 UDP_Replay

.. code-block:: yaml

      vnf_0:
        floating_ip: true
        placement: "pgrp1"
        network_ports:
          mgmt:
            - mgmt
          uplink_0:
            - xe0
          downlink_0:
            - xe1
      tg_0:
        floating_ip: true
        placement: "pgrp1"
        network_ports:
          mgmt:
            - mgmt
          uplink_0:
            - xe0
          # Trex always needs two ports
          uplink_1:
            - xe1
      tg_1:
        floating_ip: true
        placement: "pgrp1"
        network_ports:
          mgmt:
           - mgmt
          downlink_0:
           - xe0

Collectd KPIS
-------------

NSB can collect KPIs from collected.  We have support for various plugins enabled by the
Barometer project.

The default yardstick-samplevnf has collectd installed.   This allows for collecting KPIs
from the VNF.

Collecting KPIs from the NFVi is more complicated and requires manual setup.
We assume that collectd is not installed on the compute nodes.

To collectd KPIs from the NFVi compute nodes:


    * install_collectd on the compute nodes
    * create pod.yaml for the compute nodes
    * enable specific plugins depending on the vswitch and DPDK

    example pod.yaml section for Compute node running collectd.
.. code-block:: yaml

    -
      name: "compute-1"
      role: Compute
      ip: "10.1.2.3"
      user: "root"
      ssh_port: "22"
      password: ""
      collectd:
        interval: 5
        plugins:
          # for libvirtd stats
          virt: {}
          intel_pmu: {}
          ovs_stats:
            # path to OVS socket
            ovs_socket_path: /var/run/openvswitch/db.sock
          intel_rdt: {}


VNF Characterization
--------------------


NFVi Characterization
---------------------

prox setup?



Scale-Up
--------

scale-up with --task-args


Scale-Out
---------


scale-out templates
even number of TG ports required



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

