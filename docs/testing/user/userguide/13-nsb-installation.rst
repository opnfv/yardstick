.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2016-2018 Intel Corporation.

..
   Convention for heading levels in Yardstick documentation:

   =======  Heading 0 (reserved for the title in a document)
   -------  Heading 1
   ^^^^^^^  Heading 2
   +++++++  Heading 3
   '''''''  Heading 4

   Avoid deeper levels because they do not render well.


================
NSB Installation
================

.. _OVS-DPDK: http://docs.openvswitch.org/en/latest/intro/install/dpdk/
.. _devstack: https://docs.openstack.org/devstack/pike/>

Abstract
--------

The steps needed to run Yardstick with NSB testing are:

* Install Yardstick (NSB Testing).
* Setup/reference ``pod.yaml`` describing Test topology
* Create/reference the test configuration yaml file.
* Run the test case.

Prerequisites
-------------

Refer to :doc:`04-installation` for more information on Yardstick
prerequisites.

Several prerequisites are needed for Yardstick (VNF testing):

  * Python Modules: pyzmq, pika.
  * flex
  * bison
  * build-essential
  * automake
  * libtool
  * librabbitmq-dev
  * rabbitmq-server
  * collectd
  * intel-cmt-cat

Hardware & Software Ingredients
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SUT requirements:

   ======= ===================
   Item    Description
   ======= ===================
   Memory  Min 20GB
   NICs    2 x 10G
   OS      Ubuntu 16.04.3 LTS
   kernel  4.4.0-34-generic
   DPDK    17.02
   ======= ===================

Boot and BIOS settings:

   ============= =================================================
   Boot settings default_hugepagesz=1G hugepagesz=1G hugepages=16
                 hugepagesz=2M hugepages=2048 isolcpus=1-11,22-33
                 nohz_full=1-11,22-33 rcu_nocbs=1-11,22-33
                 iommu=on iommu=pt intel_iommu=on
                 Note: nohz_full and rcu_nocbs is to disable Linux
                 kernel interrupts
   BIOS          CPU Power and Performance Policy <Performance>
                 CPU C-state Disabled
                 CPU P-state Disabled
                 Enhanced Intel® Speedstep® Tech Disabl
                 Hyper-Threading Technology (If supported) Enabled
                 Virtualization Techology Enabled
                 Intel(R) VT for Direct I/O Enabled
                 Coherency Enabled
                 Turbo Boost Disabled
   ============= =================================================

Install Yardstick (NSB Testing)
-------------------------------

Download the source code and check out the latest stable branch::

.. code-block:: console

  git clone https://gerrit.opnfv.org/gerrit/yardstick
  cd yardstick
  # Switch to latest stable branch
  git checkout stable/gambia

Configure the network proxy, either using the environment variables or setting
the global environment file.

* Set environment

.. code-block::

    http_proxy='http://proxy.company.com:port'
    https_proxy='http://proxy.company.com:port'

.. code-block:: console

    export http_proxy='http://proxy.company.com:port'
    export https_proxy='http://proxy.company.com:port'

Modify the Yardstick installation inventory, used by Ansible::

  cat ./ansible/install-inventory.ini
  [jumphost]
  localhost ansible_connection=local

  [yardstick-standalone]
  yardstick-standalone-node ansible_host=192.168.1.2
  yardstick-standalone-node-2 ansible_host=192.168.1.3

  # section below is only due backward compatibility.
  # it will be removed later
  [yardstick:children]
  jumphost

  [all:vars]
  ansible_user=root
  ansible_pass=root

.. note::

   SSH access without password needs to be configured for all your nodes
   defined in ``yardstick-install-inventory.ini`` file.
   If you want to use password authentication you need to install ``sshpass``::

     sudo -EH apt-get install sshpass

To execute an installation for a BareMetal or a Standalone context::

    ./nsb_setup.sh


To execute an installation for an OpenStack context::

    ./nsb_setup.sh <path to admin-openrc.sh>

The above commands will set up Docker with the latest Yardstick code. To
execute::

  docker exec -it yardstick bash

It will also automatically download all the packages needed for NSB Testing
setup. Refer chapter :doc:`04-installation` for more on Docker

**Install Yardstick using Docker (recommended)**

Another way to execute an installation for a Bare-Metal or a Standalone context
is to use ansible script ``install.yaml``. Refer chapter :doc:`04-installation`
for more details.

System Topology
---------------

.. code-block:: console

  +----------+              +----------+
  |          |              |          |
  |          | (0)----->(0) |          |
  |    TG1   |              |    DUT   |
  |          |              |          |
  |          | (1)<-----(1) |          |
  +----------+              +----------+
  trafficgen_1                   vnf


Environment parameters and credentials
--------------------------------------

Configure yardstick.conf
^^^^^^^^^^^^^^^^^^^^^^^^

If you did not run ``yardstick env influxdb`` inside the container to generate
 ``yardstick.conf``, then create the config file manually (run inside the
container)::

    cp ./etc/yardstick/yardstick.conf.sample /etc/yardstick/yardstick.conf
    vi /etc/yardstick/yardstick.conf

Add ``trex_path``, ``trex_client_lib`` and ``bin_path`` to the ``nsb``
section::

  [DEFAULT]
  debug = True
  dispatcher = influxdb

  [dispatcher_influxdb]
  timeout = 5
  target = http://{YOUR_IP_HERE}:8086
  db_name = yardstick
  username = root
  password = root

  [nsb]
  trex_path=/opt/nsb_bin/trex/scripts
  bin_path=/opt/nsb_bin
  trex_client_lib=/opt/nsb_bin/trex_client/stl

Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  See :doc:`04-installation`

Connect to the Yardstick container::

  docker exec -it yardstick /bin/bash

If you're running ``heat`` testcases and ``nsb_setup.sh`` was not used::
  source /etc/yardstick/openstack.creds

In addition to the above, you need to se the ``EXTERNAL_NETWORK`` for
OpenStack::

  export EXTERNAL_NETWORK="<openstack public network>"

Finally, you should be able to run the testcase::

  yardstick --debug task start yardstick/samples/vnf_samples/nsut/<vnf>/<test case>

Network Service Benchmarking - Bare-Metal
-----------------------------------------

Bare-Metal Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bare-Metal 2-Node setup
+++++++++++++++++++++++
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
++++++++++++++++++++++++++++++++++++++++++++
.. code-block:: console

  +----------+              +----------+            +------------+
  |          |              |          |            |            |
  |          |              |          |            |            |
  |          | (0)----->(0) |          |            |    UDP     |
  |    TG1   |              |    DUT   |            |   Replay   |
  |          |              |          |            |            |
  |          |              |          |(1)<---->(0)|            |
  +----------+              +----------+            +------------+
  trafficgen_1                   vnf                 trafficgen_2


Bare-Metal Config pod.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^
Before executing Yardstick test cases, make sure that ``pod.yaml`` reflects the
topology and update all the required fields.::

    cp /etc/yardstick/nodes/pod.yaml.nsb.sample /etc/yardstick/nodes/pod.yaml

.. code-block:: YAML

    nodes:
    -
        name: trafficgen_1
        role: TrafficGen
        ip: 1.1.1.1
        user: root
        password: r00t
        interfaces:
            xe0:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:07:00.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 0
                local_ip: "152.16.100.20"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:01"
            xe1:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:07:00.1"
                driver:    i40e # default kernel driver
                dpdk_port_num: 1
                local_ip: "152.16.40.20"
                netmask:   "255.255.255.0"
                local_mac: "00:00.00:00:00:02"

    -
        name: vnf
        role: vnf
        ip: 1.1.1.2
        user: root
        password: r00t
        host: 1.1.1.2 #BM - host == ip, virtualized env - Host - compute node
        interfaces:
            xe0:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:07:00.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 0
                local_ip: "152.16.100.19"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:03"

            xe1:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:07:00.1"
                driver:    i40e # default kernel driver
                dpdk_port_num: 1
                local_ip: "152.16.40.19"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:04"
        routing_table:
        - network: "152.16.100.20"
          netmask: "255.255.255.0"
          gateway: "152.16.100.20"
          if: "xe0"
        - network: "152.16.40.20"
          netmask: "255.255.255.0"
          gateway: "152.16.40.20"
          if: "xe1"
        nd_route_tbl:
        - network: "0064:ff9b:0:0:0:0:9810:6414"
          netmask: "112"
          gateway: "0064:ff9b:0:0:0:0:9810:6414"
          if: "xe0"
        - network: "0064:ff9b:0:0:0:0:9810:2814"
          netmask: "112"
          gateway: "0064:ff9b:0:0:0:0:9810:2814"
          if: "xe1"


Standalone Virtualization
-------------------------

SR-IOV
^^^^^^

SR-IOV Pre-requisites
+++++++++++++++++++++

On Host, where VM is created:
 a) Create and configure a bridge named ``br-int`` for VM to connect to
    external network. Currently this can be done using VXLAN tunnel.

    Execute the following on host, where VM is created::

      ip link add type vxlan remote <Jumphost IP> local <DUT IP> id <ID: 10> dstport 4789
      brctl addbr br-int
      brctl addif br-int vxlan0
      ip link set dev vxlan0 up
      ip addr add <IP#1, like: 172.20.2.1/24> dev br-int
      ip link set dev br-int up

  .. note:: You may need to add extra rules to iptable to forward traffic.

  .. code-block:: console

    iptables -A FORWARD -i br-int -s <network ip address>/<netmask> -j ACCEPT
    iptables -A FORWARD -o br-int -d <network ip address>/<netmask> -j ACCEPT

  Execute the following on a jump host:

  .. code-block:: console

      ip link add type vxlan remote <DUT IP> local <Jumphost IP> id <ID: 10> dstport 4789
      ip addr add <IP#2, like: 172.20.2.2/24> dev vxlan0
      ip link set dev vxlan0 up

  .. note:: Host and jump host are different baremetal servers.

 b) Modify test case management CIDR.
    IP addresses IP#1, IP#2 and CIDR must be in the same network.

  .. code-block:: YAML

    servers:
      vnf:
        network_ports:
          mgmt:
            cidr: '1.1.1.7/24'

 c) Build guest image for VNF to run.
    Most of the sample test cases in Yardstick are using a guest image called
    ``yardstick-nsb-image`` which deviates from an Ubuntu Cloud Server image
    Yardstick has a tool for building this custom image with SampleVNF.
    It is necessary to have ``sudo`` rights to use this tool.

   Also you may need to install several additional packages to use this tool, by
   following the commands below::

      sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

   This image can be built using the following command in the directory where
   Yardstick is installed::

      export YARD_IMG_ARCH='amd64'
      sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers

   For instructions on generating a cloud image using Ansible, refer to
   :doc:`04-installation`.

   for more details refer to chapter :doc:`04-installation`

   .. note:: VM should be build with static IP and be accessible from the
      Yardstick host.


SR-IOV Config pod.yaml describing Topology
++++++++++++++++++++++++++++++++++++++++++

SR-IOV 2-Node setup
+++++++++++++++++++
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
  +----------+               +-------------------------+
  |          |               |       ^          ^      |
  |          |               |       |          |      |
  |          | (0)<----->(0) | ------    SUT    |      |
  |    TG1   |               |                  |      |
  |          | (n)<----->(n) | -----------------       |
  |          |               |                         |
  +----------+               +-------------------------+
  trafficgen_1                          host



SR-IOV 3-Node setup - Correlated Traffic
++++++++++++++++++++++++++++++++++++++++
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
  +----------+               +---------------------+            +--------------+
  |          |               |     ^          ^    |            |              |
  |          |               |     |          |    |            |              |
  |          | (0)<----->(0) |-----           |    |            |     TG2      |
  |    TG1   |               |         SUT    |    |            | (UDP Replay) |
  |          |               |                |    |            |              |
  |          | (n)<----->(n) |                -----| (n)<-->(n) |              |
  +----------+               +---------------------+            +--------------+
  trafficgen_1                          host                      trafficgen_2

Before executing Yardstick test cases, make sure that ``pod.yaml`` reflects the
topology and update all the required fields.

.. code-block:: console

    cp <yardstick>/etc/yardstick/nodes/standalone/trex_bm.yaml.sample /etc/yardstick/nodes/standalone/pod_trex.yaml
    cp <yardstick>/etc/yardstick/nodes/standalone/host_sriov.yaml /etc/yardstick/nodes/standalone/host_sriov.yaml

.. note:: Update all the required fields like ip, user, password, pcis, etc...

SR-IOV Config pod_trex.yaml
+++++++++++++++++++++++++++

.. code-block:: YAML

    nodes:
    -
        name: trafficgen_1
        role: TrafficGen
        ip: 1.1.1.1
        user: root
        password: r00t
        key_filename: /root/.ssh/id_rsa
        interfaces:
            xe0:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:07:00.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 0
                local_ip: "152.16.100.20"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:01"
            xe1:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:07:00.1"
                driver:    i40e # default kernel driver
                dpdk_port_num: 1
                local_ip: "152.16.40.20"
                netmask:   "255.255.255.0"
                local_mac: "00:00.00:00:00:02"

SR-IOV Config host_sriov.yaml
+++++++++++++++++++++++++++++

.. code-block:: YAML

    nodes:
    -
       name: sriov
       role: Sriov
       ip: 192.168.100.101
       user: ""
       password: ""

SR-IOV testcase update:
``<yardstick>/samples/vnf_samples/nsut/vfw/tc_sriov_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``

Update contexts section
'''''''''''''''''''''''

.. code-block:: YAML

  contexts:
   - name: yardstick
     type: Node
     file: /etc/yardstick/nodes/standalone/pod_trex.yaml
   - type: StandaloneSriov
     file: /etc/yardstick/nodes/standalone/host_sriov.yaml
     name: yardstick
     vm_deploy: True
     flavor:
       images: "/var/lib/libvirt/images/ubuntu.qcow2"
       ram: 4096
       extra_specs:
         hw:cpu_sockets: 1
         hw:cpu_cores: 6
         hw:cpu_threads: 2
       user: "" # update VM username
       password: "" # update password
     servers:
       vnf:
         network_ports:
           mgmt:
             cidr: '1.1.1.61/24'  # Update VM IP address, if static, <ip>/<mask> or if dynamic, <start of ip>/<mask>
           xe0:
             - uplink_0
           xe1:
             - downlink_0
     networks:
       uplink_0:
         phy_port: "0000:05:00.0"
         vpci: "0000:00:07.0"
         cidr: '152.16.100.10/24'
         gateway_ip: '152.16.100.20'
       downlink_0:
         phy_port: "0000:05:00.1"
         vpci: "0000:00:08.0"
         cidr: '152.16.40.10/24'
         gateway_ip: '152.16.100.20'


OVS-DPDK
^^^^^^^^

OVS-DPDK Pre-requisites
+++++++++++++++++++++++

On Host, where VM is created:
 a) Create and configure a bridge named ``br-int`` for VM to connect to
    external network. Currently this can be done using VXLAN tunnel.

    Execute the following on host, where VM is created:

  .. code-block:: console

      ip link add type vxlan remote <Jumphost IP> local <DUT IP> id <ID: 10> dstport 4789
      brctl addbr br-int
      brctl addif br-int vxlan0
      ip link set dev vxlan0 up
      ip addr add <IP#1, like: 172.20.2.1/24> dev br-int
      ip link set dev br-int up

  .. note:: May be needed to add extra rules to iptable to forward traffic.

  .. code-block:: console

    iptables -A FORWARD -i br-int -s <network ip address>/<netmask> -j ACCEPT
    iptables -A FORWARD -o br-int -d <network ip address>/<netmask> -j ACCEPT

  Execute the following on a jump host:

  .. code-block:: console

      ip link add type vxlan remote <DUT IP> local <Jumphost IP> id <ID: 10> dstport 4789
      ip addr add <IP#2, like: 172.20.2.2/24> dev vxlan0
      ip link set dev vxlan0 up

  .. note:: Host and jump host are different baremetal servers.

 b) Modify test case management CIDR.
    IP addresses IP#1, IP#2 and CIDR must be in the same network.

  .. code-block:: YAML

    servers:
      vnf:
        network_ports:
          mgmt:
            cidr: '1.1.1.7/24'

 c) Build guest image for VNF to run.
    Most of the sample test cases in Yardstick are using a guest image called
    ``yardstick-nsb-image`` which deviates from an Ubuntu Cloud Server image
    Yardstick has a tool for building this custom image with SampleVNF.
    It is necessary to have ``sudo`` rights to use this tool.

   You may need to install several additional packages to use this tool, by
   following the commands below::

      sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

   This image can be built using the following command in the directory where
   Yardstick is installed::

      export YARD_IMG_ARCH='amd64'
      sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers
      sudo tools/yardstick-img-dpdk-modify tools/ubuntu-server-cloudimg-samplevnf-modify.sh

   for more details refer to chapter :doc:`04-installation`

   .. note::  VM should be build with static IP and should be accessible from
      yardstick host.

3. OVS & DPDK version.
   * OVS 2.7 and DPDK 16.11.1 above version is supported

4. Setup `OVS-DPDK`_ on host.


OVS-DPDK Config pod.yaml describing Topology
++++++++++++++++++++++++++++++++++++++++++++

OVS-DPDK 2-Node setup
+++++++++++++++++++++

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
++++++++++++++++++++++++++++++++++++++++++

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
  +----------+               +-------------------------+          +------------+
  |          |               |       ^          ^      |          |            |
  |          |               |       |          |      |          |            |
  |          | (0)<----->(0) | ------           |      |          |    TG2     |
  |    TG1   |               |          SUT     |      |          |(UDP Replay)|
  |          |               |      (ovs-dpdk)  |      |          |            |
  |          | (n)<----->(n) |                  ------ |(n)<-->(n)|            |
  +----------+               +-------------------------+          +------------+
  trafficgen_1                          host                       trafficgen_2


Before executing Yardstick test cases, make sure that the ``pod.yaml`` reflects
the topology and update all the required fields::

  cp <yardstick>/etc/yardstick/nodes/standalone/trex_bm.yaml.sample /etc/yardstick/nodes/standalone/pod_trex.yaml
  cp <yardstick>/etc/yardstick/nodes/standalone/host_ovs.yaml /etc/yardstick/nodes/standalone/host_ovs.yaml

.. note:: Update all the required fields like ip, user, password, pcis, etc...

OVS-DPDK Config pod_trex.yaml
+++++++++++++++++++++++++++++

.. code-block:: YAML

    nodes:
    -
      name: trafficgen_1
      role: TrafficGen
      ip: 1.1.1.1
      user: root
      password: r00t
      interfaces:
          xe0:  # logical name from topology.yaml and vnfd.yaml
              vpci:      "0000:07:00.0"
              driver:    i40e # default kernel driver
              dpdk_port_num: 0
              local_ip: "152.16.100.20"
              netmask:   "255.255.255.0"
              local_mac: "00:00:00:00:00:01"
          xe1:  # logical name from topology.yaml and vnfd.yaml
              vpci:      "0000:07:00.1"
              driver:    i40e # default kernel driver
              dpdk_port_num: 1
              local_ip: "152.16.40.20"
              netmask:   "255.255.255.0"
              local_mac: "00:00.00:00:00:02"

OVS-DPDK Config host_ovs.yaml
+++++++++++++++++++++++++++++

.. code-block:: YAML

    nodes:
    -
       name: ovs_dpdk
       role: OvsDpdk
       ip: 192.168.100.101
       user: ""
       password: ""

ovs_dpdk testcase update:
``<yardstick>/samples/vnf_samples/nsut/vfw/tc_ovs_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``

Update contexts section
'''''''''''''''''''''''

.. code-block:: YAML

  contexts:
   - name: yardstick
     type: Node
     file: /etc/yardstick/nodes/standalone/pod_trex.yaml
   - type: StandaloneOvsDpdk
     name: yardstick
     file: /etc/yardstick/nodes/standalone/pod_ovs.yaml
     vm_deploy: True
     ovs_properties:
       version:
         ovs: 2.7.0
         dpdk: 16.11.1
       pmd_threads: 2
       ram:
         socket_0: 2048
         socket_1: 2048
       queues: 4
       vpath: "/usr/local"

     flavor:
       images: "/var/lib/libvirt/images/ubuntu.qcow2"
       ram: 4096
       extra_specs:
         hw:cpu_sockets: 1
         hw:cpu_cores: 6
         hw:cpu_threads: 2
       user: "" # update VM username
       password: "" # update password
     servers:
       vnf:
         network_ports:
           mgmt:
             cidr: '1.1.1.61/24'  # Update VM IP address, if static, <ip>/<mask> or if dynamic, <start of ip>/<mask>
           xe0:
             - uplink_0
           xe1:
             - downlink_0
     networks:
       uplink_0:
         phy_port: "0000:05:00.0"
         vpci: "0000:00:07.0"
         cidr: '152.16.100.10/24'
         gateway_ip: '152.16.100.20'
       downlink_0:
         phy_port: "0000:05:00.1"
         vpci: "0000:00:08.0"
         cidr: '152.16.40.10/24'
         gateway_ip: '152.16.100.20'


OpenStack with SR-IOV support
-----------------------------

This section describes how to run a Sample VNF test case, using Heat context,
with SR-IOV. It also covers how to install OpenStack in Ubuntu 16.04, using
DevStack, with SR-IOV support.


Single node OpenStack with external TG
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

                                 +----------------------------+
                                 |OpenStack(DevStack)         |
                                 |                            |
                                 |   +--------------------+   |
                                 |   |sample-VNF VM       |   |
                                 |   |                    |   |
                                 |   |        DUT         |   |
                                 |   |       (VNF)        |   |
                                 |   |                    |   |
                                 |   +--------+  +--------+   |
                                 |   | VF NIC |  | VF NIC |   |
                                 |   +-----+--+--+----+---+   |
                                 |         ^          ^       |
                                 |         |          |       |
  +----------+                   +---------+----------+-------+
  |          |                   |        VF0        VF1      |
  |          |                   |         ^          ^       |
  |          |                   |         |   SUT    |       |
  |    TG    | (PF0)<----->(PF0) +---------+          |       |
  |          |                   |                    |       |
  |          | (PF1)<----->(PF1) +--------------------+       |
  |          |                   |                            |
  +----------+                   +----------------------------+
  trafficgen_1                                 host


Host pre-configuration
++++++++++++++++++++++

.. warning:: The following configuration requires sudo access to the system.
   Make sure that your user have the access.

Enable the Intel VT-d or AMD-Vi extension in the BIOS. Some system
manufacturers disable this extension by default.

Activate the Intel VT-d or AMD-Vi extension in the kernel by modifying the GRUB
config file ``/etc/default/grub``.

For the Intel platform::

  ...
  GRUB_CMDLINE_LINUX_DEFAULT="intel_iommu=on"
  ...

For the AMD platform::

  ...
  GRUB_CMDLINE_LINUX_DEFAULT="amd_iommu=on"
  ...

Update the grub configuration file and restart the system:

.. warning:: The following command will reboot the system.

.. code:: bash

  sudo update-grub
  sudo reboot

Make sure the extension has been enabled::

  sudo journalctl -b 0 | grep -e IOMMU -e DMAR

  Feb 06 14:50:14 hostname kernel: ACPI: DMAR 0x000000006C406000 0001E0 (v01 INTEL  S2600WF  00000001 INTL 20091013)
  Feb 06 14:50:14 hostname kernel: DMAR: IOMMU enabled
  Feb 06 14:50:14 hostname kernel: DMAR: Host address width 46
  Feb 06 14:50:14 hostname kernel: DMAR: DRHD base: 0x000000d37fc000 flags: 0x0
  Feb 06 14:50:14 hostname kernel: DMAR: dmar0: reg_base_addr d37fc000 ver 1:0 cap 8d2078c106f0466 ecap f020de
  Feb 06 14:50:14 hostname kernel: DMAR: DRHD base: 0x000000e0ffc000 flags: 0x0
  Feb 06 14:50:14 hostname kernel: DMAR: dmar1: reg_base_addr e0ffc000 ver 1:0 cap 8d2078c106f0466 ecap f020de
  Feb 06 14:50:14 hostname kernel: DMAR: DRHD base: 0x000000ee7fc000 flags: 0x0

.. TODO: Refer to the yardstick installation guide for proxy set up

Setup system proxy (if needed). Add the following configuration into the
``/etc/environment`` file:

.. note:: The proxy server name/port and IPs should be changed according to
  actual/current proxy configuration in the lab.

.. code:: bash

  export http_proxy=http://proxy.company.com:port
  export https_proxy=http://proxy.company.com:port
  export ftp_proxy=http://proxy.company.com:port
  export no_proxy=localhost,127.0.0.1,company.com,<IP-OF-HOST1>,<IP-OF-HOST2>,...
  export NO_PROXY=localhost,127.0.0.1,company.com,<IP-OF-HOST1>,<IP-OF-HOST2>,...

Upgrade the system:

.. code:: bash

  sudo -EH apt-get update
  sudo -EH apt-get upgrade
  sudo -EH apt-get dist-upgrade

Install dependencies needed for DevStack

.. code:: bash

  sudo -EH apt-get install python python-dev python-pip

Setup SR-IOV ports on the host:

.. note:: The ``enp24s0f0``, ``enp24s0f1`` are physical function (PF) interfaces
  on a host and ``enp24s0f3`` is a public interface used in OpenStack, so the
  interface names should be changed according to the HW environment used for
  testing.

.. code:: bash

  sudo ip link set dev enp24s0f0 up
  sudo ip link set dev enp24s0f1 up
  sudo ip link set dev enp24s0f3 up

  # Create VFs on PF
  echo 2 | sudo tee /sys/class/net/enp24s0f0/device/sriov_numvfs
  echo 2 | sudo tee /sys/class/net/enp24s0f1/device/sriov_numvfs


DevStack installation
+++++++++++++++++++++

If you want to try out NSB, but don't have OpenStack set-up, you can use
`Devstack`_ to install OpenStack on a host. Please note, that the
``stable/pike`` branch of devstack repo should be used during the installation.
The required ``local.conf`` configuration file are described below.

DevStack configuration file:

.. note:: Update the devstack configuration file by replacing angluar brackets
  with a short description inside.

.. note:: Use ``lspci | grep Ether`` & ``lspci -n | grep <PCI ADDRESS>``
  commands to get device and vendor id of the virtual function (VF).

.. literalinclude:: code/single-devstack-local.conf
   :language: console

Start the devstack installation on a host.

TG host configuration
+++++++++++++++++++++

Yardstick automatically installs and configures Trex traffic generator on TG
host based on provided POD file (see below). Anyway, it's recommended to check
the compatibility of the installed NIC on the TG server with software Trex
using the `manual <https://trex-tgn.cisco.com/trex/doc/trex_manual.html>`_.

Run the Sample VNF test case
++++++++++++++++++++++++++++

There is an example of Sample VNF test case ready to be executed in an
OpenStack environment with SR-IOV support: ``samples/vnf_samples/nsut/vfw/
tc_heat_sriov_external_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``.

Install Yardstick using `Install Yardstick (NSB Testing)`_ steps for OpenStack
context.

Create pod file for TG in the yardstick repo folder located in the yardstick
container:

.. note:: The ``ip``, ``user``, ``password`` and ``vpci`` fields show be  changed
  according to HW environment used for the testing. Use ``lshw -c network -businfo``
  command to get the PF PCI address for ``vpci`` field.

.. literalinclude:: code/single-yardstick-pod.conf
   :language: console

Run the Sample vFW RFC2544 SR-IOV TC (``samples/vnf_samples/nsut/vfw/
tc_heat_sriov_external_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``) in the heat
context using steps described in `NS testing - using yardstick CLI`_ section.


Multi node OpenStack TG and VNF setup (two nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

  +----------------------------+                   +----------------------------+
  |OpenStack(DevStack)         |                   |OpenStack(DevStack)         |
  |                            |                   |                            |
  |   +--------------------+   |                   |   +--------------------+   |
  |   |sample-VNF VM       |   |                   |   |sample-VNF VM       |   |
  |   |                    |   |                   |   |                    |   |
  |   |         TG         |   |                   |   |        DUT         |   |
  |   |    trafficgen_1    |   |                   |   |       (VNF)        |   |
  |   |                    |   |                   |   |                    |   |
  |   +--------+  +--------+   |                   |   +--------+  +--------+   |
  |   | VF NIC |  | VF NIC |   |                   |   | VF NIC |  | VF NIC |   |
  |   +----+---+--+----+---+   |                   |   +-----+--+--+----+---+   |
  |        ^           ^       |                   |         ^          ^       |
  |        |           |       |                   |         |          |       |
  +--------+-----------+-------+                   +---------+----------+-------+
  |       VF0         VF1      |                   |        VF0        VF1      |
  |        ^           ^       |                   |         ^          ^       |
  |        |    SUT2   |       |                   |         |   SUT1   |       |
  |        |           +-------+ (PF0)<----->(PF0) +---------+          |       |
  |        |                   |                   |                    |       |
  |        +-------------------+ (PF1)<----->(PF1) +--------------------+       |
  |                            |                   |                            |
  +----------------------------+                   +----------------------------+
           host2 (compute)                               host1 (controller)


Controller/Compute pre-configuration
++++++++++++++++++++++++++++++++++++

Pre-configuration of the controller and compute hosts are the same as
described in `Host pre-configuration`_ section.

DevStack configuration
++++++++++++++++++++++

A reference ``local.conf`` for deploying OpenStack in a multi-host environment
using `Devstack`_ is shown in this section. The ``stable/pike`` branch of
devstack repo should be used during the installation.

.. note:: Update the devstack configuration files by replacing angluar brackets
  with a short description inside.

.. note:: Use ``lspci | grep Ether`` & ``lspci -n | grep <PCI ADDRESS>``
  commands to get device and vendor id of the virtual function (VF).

DevStack configuration file for controller host:

.. literalinclude:: code/multi-devstack-controller-local.conf
   :language: console

DevStack configuration file for compute host:

.. literalinclude:: code/multi-devstack-compute-local.conf
   :language: console

Start the devstack installation on the controller and compute hosts.

Run the sample vFW TC
+++++++++++++++++++++

Install Yardstick using `Install Yardstick (NSB Testing)`_ steps for OpenStack
context.

Run the sample vFW RFC2544 SR-IOV test case
(``samples/vnf_samples/nsut/vfw/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``)
in the heat context using steps described in
`NS testing - using yardstick CLI`_ section and the following Yardstick command
line arguments:

.. code:: bash

  yardstick -d task start --task-args='{"provider": "sriov"}' \
  samples/vnf_samples/nsut/vfw/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex.yaml


Enabling other Traffic generators
---------------------------------

IxLoad
~~~~~~

1. Software needed: IxLoadAPI ``<IxLoadTclApi verson>Linux64.bin.tgz`` and
   ``<IxOS version>Linux64.bin.tar.gz`` (Download from ixia support site)
   Install - ``<IxLoadTclApi verson>Linux64.bin.tgz`` and
   ``<IxOS version>Linux64.bin.tar.gz``
   If the installation was not done inside the container, after installing
   the IXIA client, check ``/opt/ixia/ixload/<ver>/bin/ixloadpython`` and make
   sure you can run this cmd inside the yardstick container. Usually user is
   required to copy or link ``/opt/ixia/python/<ver>/bin/ixiapython`` to
   ``/usr/bin/ixiapython<ver>`` inside the container.

2. Update ``pod_ixia.yaml`` file with ixia details.

  .. code-block:: console

    cp <repo>/etc/yardstick/nodes/pod.yaml.nsb.sample.ixia \
      etc/yardstick/nodes/pod_ixia.yaml

  Config ``pod_ixia.yaml``

  .. literalinclude:: code/pod_ixia.yaml
     :language: console

  for sriov/ovs_dpdk pod files, please refer to `Standalone Virtualization`_
  for ovs-dpdk/sriov configuration

3. Start IxOS TCL Server (Install 'Ixia IxExplorer IxOS <version>')
   You will also need to configure the IxLoad machine to start the IXIA
   IxosTclServer. This can be started like so:

   * Connect to the IxLoad machine using RDP
   * Go to:
     ``Start->Programs->Ixia->IxOS->IxOS 8.01-GA-Patch1->Ixia Tcl Server IxOS 8.01-GA-Patch1``
     or
     ``C:\Program Files (x86)\Ixia\IxOS\8.01-GA-Patch1\ixTclServer.exe``

4. Create a folder ``Results`` in c:\ and share the folder on the network.

5. Execute testcase in samplevnf folder e.g.
   ``<repo>/samples/vnf_samples/nsut/vfw/tc_baremetal_http_ixload_1b_Requests-65000_Concurrency.yaml``

IxNetwork
^^^^^^^^^

IxNetwork testcases use IxNetwork API Python Bindings module, which is
installed as part of the requirements of the project.

1. Update ``pod_ixia.yaml`` file with ixia details.

  .. code-block:: console

    cp <repo>/etc/yardstick/nodes/pod.yaml.nsb.sample.ixia \
    etc/yardstick/nodes/pod_ixia.yaml

  Configure ``pod_ixia.yaml``

  .. literalinclude:: code/pod_ixia.yaml
     :language: console

  for sriov/ovs_dpdk pod files, please refer to above
  `Standalone Virtualization`_ for ovs-dpdk/sriov configuration

2. Start IxNetwork TCL Server
   You will also need to configure the IxNetwork machine to start the IXIA
   IxNetworkTclServer. This can be started like so:

    * Connect to the IxNetwork machine using RDP
    * Go to:
      ``Start->Programs->Ixia->IxNetwork->IxNetwork 7.21.893.14 GA->IxNetworkTclServer``
      (or ``IxNetworkApiServer``)

3. Execute testcase in samplevnf folder e.g.
   ``<repo>/samples/vnf_samples/nsut/vfw/tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml``

Spirent Landslide
-----------------

In order to use Spirent Landslide for vEPC testcases, some dependencies have
to be preinstalled and properly configured.

- Java

    32-bit Java installation is required for the Spirent Landslide TCL API.

    | ``$ sudo apt-get install openjdk-8-jdk:i386``

    .. important::
      Make sure ``LD_LIBRARY_PATH`` is pointing to 32-bit JRE. For more details
      check `Linux Troubleshooting <http://TAS_HOST_IP/tclapiinstall.html#trouble>`
      section of installation instructions.

- LsApi (Tcl API module)

    Follow Landslide documentation for detailed instructions on Linux
    installation of Tcl API and its dependencies
    ``http://TAS_HOST_IP/tclapiinstall.html``.
    For working with LsApi Python wrapper only steps 1-5 are required.

    .. note:: After installation make sure your API home path is included in
      ``PYTHONPATH`` environment variable.

    .. important::
    The current version of LsApi module has an issue with reading LD_LIBRARY_PATH.
    For LsApi module to initialize correctly following lines (184-186) in
    lsapi.py

    .. code-block:: python

        ldpath = os.environ.get('LD_LIBRARY_PATH', '')
        if ldpath == '':
         environ['LD_LIBRARY_PATH'] = environ['LD_LIBRARY_PATH'] + ':' + ldpath

    should be changed to:

    .. code-block:: python

        ldpath = os.environ.get('LD_LIBRARY_PATH', '')
        if not ldpath == '':
               environ['LD_LIBRARY_PATH'] = environ['LD_LIBRARY_PATH'] + ':' + ldpath

.. note:: The Spirent landslide TCL software package needs to be updated in case
  the user upgrades to a new version of Spirent landslide software.
