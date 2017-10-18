.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2016-2017 Intel Corporation.

Yardstick - NSB Testing -Installation
=====================================

Abstract
--------

The Network Service Benchmarking (NSB) extends the yardstick framework to do
VNF characterization and benchmarking in three different execution
environments viz., bare metal i.e. native Linux environment, standalone virtual
environment and managed virtualized environment (e.g. Open stack etc.).
It also brings in the capability to interact with external traffic generators
both hardware & software based for triggering and validating the traffic
according to user defined profiles.

The steps needed to run Yardstick with NSB testing are:

* Install Yardstick (NSB Testing).
* Setup pod.yaml describing Test topology
* Create the test configuration yaml file.
* Run the test case.


Prerequisites
-------------

Refer chapter Yardstick Instalaltion for more information on yardstick
prerequisites

Several prerequisites are needed for Yardstick(VNF testing):

- Python Modules: pyzmq, pika.

- flex

- bison

- build-essential

- automake

- libtool

- librabbitmq-dev

- rabbitmq-server

- collectd

- intel-cmt-cat

Hardware & Software Ingredients
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SUT requirements:

::

   +-----------+------------------+
   | Item      | Description      |
   +-----------+------------------+
   | Memory    | Min 20GB         |
   +-----------+------------------+
   | NICs      | 2 x 10G          |
   +-----------+------------------+
   | OS        | Ubuntu 16.04 LTS |
   +-----------+------------------+
   | kernel    |  4.4.0-34-generic|
   +-----------+------------------+
   | DPDK      | 17.02            |
   +-----------+------------------+

Boot and BIOS settings:

::

   +------------------+---------------------------------------------------+
   | Boot settings    | default_hugepagesz=1G hugepagesz=1G hugepages=16  |
   |                  | hugepagesz=2M hugepages=2048 isolcpus=1-11,22-33  |
   |                  | nohz_full=1-11,22-33 rcu_nocbs=1-11,22-33         |
   |                  | Note: nohz_full and rcu_nocbs is to disable Linux*|
   |                  | kernel interrupts, and it’s import                |
   +------------------+---------------------------------------------------+
   |BIOS              | CPU Power and Performance Policy <Performance>    |
   |                  | CPU C-state Disabled                              |
   |                  | CPU P-state Disabled                              |
   |                  | Enhanced Intel® Speedstep® Tech Disabled          |
   |                  | Hyper-Threading Technology (If supported) Enable  |
   |                  | Virtualization Techology Enable                   |
   |                  | Coherency Enable                                  |
   |                  | Turbo Boost Disabled                              |
   +------------------+---------------------------------------------------+



Install Yardstick (NSB Testing)
-------------------------------

Using Docker
------------
Refer chapter :doc:`04-installation` for more on docker **Install Yardstick using Docker (**recommended**)**

Install directly in Ubuntu
--------------------------
.. _install-framework:

Alternatively you can install Yardstick framework directly in Ubuntu or in an Ubuntu Docker image. No matter which way you choose to install Yardstick, the following installation steps are identical.

If you choose to use the Ubuntu Docker image, you can pull the Ubuntu
Docker image from Docker hub::

  docker pull ubuntu:16.04

Install Yardstick
^^^^^^^^^^^^^^^^^^^^^

Download the source code and install Yardstick from it::

  git clone https://gerrit.opnfv.org/gerrit/yardstick
  export YARDSTICK_REPO_DIR=~/yardstick

  cd yardstick
  # For BareMetal or Standalone Virtualization
  ./nsb_setup.sh

  # For Openstack
  ./nsb_setup.sh <path to admin-openrc.sh>

Above command setup docker with latest yardstick code. To execute

  docker exec -it yardstick bash

It will also automatically download all the packages needed for NSB Testing setup.

System Topology:
-----------------

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

Environment variables
^^^^^^^^^^^^^^^^^^^^^

Before running Yardstick (NSB Testing) it is necessary to export traffic
generator libraries.::

    source ~/.bash_profile

Config yardstick conf
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    cp ./etc/yardstick/yardstick.conf.sample /etc/yardstick/yardstick.conf
    vi /etc/yardstick/yardstick.conf

Add trex_path, trex_client_lib and bin_path in 'nsb' section.

::

  [DEFAULT]
  debug = True
  dispatcher = file, influxdb

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

Network Service Benchmarking - Bare-Metal
-----------------------------------------

Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

2-Node setup:
^^^^^^^^^^^^^
.. code-block:: console
  +----------+              +----------+
  |          |              |          |
  |          | (0)----->(0) |          |
  |    TG1   |              |    DUT   |
  |          |              |          |
  |          | (n)<-----(n) |          |
  +----------+              +----------+
  trafficgen_1                   vnf

3-Node setup - Correlated Traffic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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

Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.::

    cp /etc/yardstick/nodes/pod.yaml.nsb.sample /etc/yardstick/nodes/pod.yaml

Config pod.yaml

::

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

Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  docker exec -it yardstick bash
  PYTHONPATH: ". ~/.bash_profile"
  cd /home/opnfv/repos/yardstick

 Execute command: ./yardstick/cmd/NSPerf.py -h
      ./yardstick/cmd/NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./yardstick/cmd/NSBperf.py --vnf vpe --test tc_baremetal_rfc2544_ipv4_1flow_64B.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. /home/opnfv/repos/yardstick/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>

Network Service Benchmarking - Standalone Virtualization
--------------------------------------------------------

SRIOV:
-----

Pre-requisites
^^^^^^^^^^^^^^

On Host:
 a) Create a bridge for VM to connect to external network
    brctl addbr br-int
    brctl addif br-int <interface_name>    #This interface is connected to internet

 b) Build guest image for VNF to run.
    Most of the sample test cases in Yardstick are using a guest image called
    ``yardstick-image`` which deviates from an Ubuntu Cloud Server image
    Yardstick has a tool for building this custom image with samplevnf.
    It is necessary to have ``sudo`` rights to use this tool.

    Also you may need to install several additional packages to use this tool, by
    follwing the commands below::

       sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

    This image can be built using the following command in the directory where Yardstick is installed::

       export YARD_IMG_ARCH='amd64'
       sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers
       Please use ansible script to generate a cloud image refer :doc:`04-installation`

    for more details refer chapter :doc:`04-installation``

Note: VM should be build with static IP and should be accessiable from yardstick host.

Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

2-Node setup:
^^^^^^^^^^^^^
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


3-Node setup - Correlated Traffic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
  +----------+               +-------------------------+          +------------+
  |          |               |       ^          ^      |          |            |
  |          |               |       |          |      |          |            |
  |          | (0)<----->(0) | ------           |      |          |    TG2     |
  |    TG1   |               |           SUT    |      |          |(UDP Replay)|
  |          |               |                  |      |          |            |
  |          | (n)<----->(n) |                  ------ |(n)<-->(n)|            |
  +----------+               +-------------------------+          +------------+
  trafficgen_1                          host                       trafficgen_2

Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.

::

    cp <yardstick>/etc/yardstick/nodes/standalone/trex_bm.yaml.sample /etc/yardstick/nodes/standalone/pod_trex.yaml
    cp <yardstick>/etc/yardstick/nodes/standalone/host_sriov.yaml /etc/yardstick/nodes/standalone/host_sriov.yaml

Note: Update all the required fields like ip, user, password, pcis, etc...
Config pod_trex.yaml

::

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

Config host_sriov.yaml

::

    nodes:
    -
       name: sriov
       role: Sriov
       ip: 192.168.100.101
       user: ""
       password: ""

Sriov testcase update: <yardstick>/samples/vnf_samples/nsut/vfw/tc_sriov_rfc2544_ipv4_1rule_1flow_64B_trex.yaml

::

  Update "contexts" section
  -------------------------

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


Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  docker exec -it yardstick bash
  PYTHONPATH: ". ~/.bash_profile"
  cd /home/opnfv/repos/yardstick

 Execute command: ./yardstick/cmd/NSPerf.py -h
      ./yardstick/cmd/NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./yardstick/cmd/NSBperf.py --vnf vfw --test tc_sriov_rfc2544_ipv4_1rule_1flow_64B_trex.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. <yardstick repo>/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>

OVS-DPDK:
---------

Pre-requisites
^^^^^^^^^^^^^^

On Host:
 a) Create a bridge for VM to connect to external network
    brctl addbr br-int
    brctl addif br-int <interface_name>    #This interface is connected to internet

 b) Build guest image for VNF to run.
    Most of the sample test cases in Yardstick are using a guest image called
    ``yardstick-image`` which deviates from an Ubuntu Cloud Server image
    Yardstick has a tool for building this custom image with samplevnf.
    It is necessary to have ``sudo`` rights to use this tool.

    Also you may need to install several additional packages to use this tool, by
    follwing the commands below::

       sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

    This image can be built using the following command in the directory where Yardstick is installed::

       export YARD_IMG_ARCH='amd64'
       sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers
       sudo tools/yardstick-img-dpdk-modify tools/ubuntu-server-cloudimg-samplevnf-modify.sh

    for more details refer chapter :doc:`04-installation``

Note: VM should be build with static IP and should be accessiable from yardstick host.

  c) OVS & DPDK version.
     - OVS 2.7 and DPDK 16.11.1 above version is supported

  d) Setup OVS/DPDK on host.
     Please refer below link on how to setup .. _ovs-dpdk: http://docs.openvswitch.org/en/latest/intro/install/dpdk/

Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

2-Node setup:
^^^^^^^^^^^^^

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


3-Node setup - Correlated Traffic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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


Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.

::

  cp <yardstick>/etc/yardstick/nodes/standalone/trex_bm.yaml.sample /etc/yardstick/nodes/standalone/pod_trex.yaml
  cp <yardstick>/etc/yardstick/nodes/standalone/host_ovs.yaml /etc/yardstick/nodes/standalone/host_ovs.yaml

Note: Update all the required fields like ip, user, password, pcis, etc...
Config pod_trex.yaml

::

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

Config host_ovs.yaml

::

    nodes:
    -
       name: ovs_dpdk
       role: OvsDpdk
       ip: 192.168.100.101
       user: ""
       password: ""

ovs_dpdk testcase update: <yardstick>/samples/vnf_samples/nsut/vfw/tc_ovs_rfc2544_ipv4_1rule_1flow_64B_trex.yaml

::

  Update "contexts" section
  -------------------------

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

Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  docker exec -it yardstick bash
  PYTHONPATH: ". ~/.bash_profile"
  cd /home/opnfv/repos/yardstick

 Execute command: ./NSPerf.py -h
      ./NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./NSBperf.py --vnf vfw --test tc_ovs_rfc2544_ipv4_1flow_64B.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. /home/opnfv/repos/yardstick/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>


Enabling other Traffic generator
================================

IxLoad:
---------

Software required for IxLoad
-----------------------------

1. Software needed : IxLoadAPI <IxLoadTclApi verson>Linux64.bin.tgz and <IxOS version>Linux64.bin.tar.gz (Download from ixia support site)
                     Install - <IxLoadTclApi verson>Linux64.bin.tgz & <IxOS version>Linux64.bin.tar.gz
4. Update pod.yaml file with ixia details.


2. Update pod_ixia.yaml file with ixia details.
   cp <repo>/etc/yardstick/nodes/pod.yaml.nsb.sample.ixia etc/yardstick/nodes/pod_ixia.yaml

   Config pod_ixia.yaml
   ::

     nodes:
        -
            name: trafficgen_1
            role: IxNet
            ip: 1.2.1.1 #ixia machine ip
            user: user
            password: r00t
            key_filename: /root/.ssh/id_rsa
            tg_config:
                ixchassis: "1.2.1.7" #ixia chassis ip
                tcl_port: "8009" # tcl server port
                lib_path: "/opt/ixia/ixos-api/8.01.0.2/lib/ixTcl1.0"
                root_dir: "/opt/ixia/ixos-api/8.01.0.2/"
                py_bin_path: "/opt/ixia/ixload/8.01.106.3/bin/"
                py_lib_path: "/opt/ixia/ixnetwork/8.01.1029.14/lib/PythonApi"
                dut_result_dir: "/mnt/ixia"
                version: 8.1
            interfaces:
                xe0:  # logical name from topology.yaml and vnfd.yaml
                    vpci: "2:5" # Card:port
                    driver:    "none"
                    dpdk_port_num: 0
                    local_ip: "152.16.100.20"
                    netmask:   "255.255.0.0"
                    local_mac: "00:98:10:64:14:00"
                xe1:  # logical name from topology.yaml and vnfd.yaml
                    vpci: "2:6" # [(Card, port)]
                    driver:    "none"
                    dpdk_port_num: 1
                    local_ip: "152.40.40.20"
                    netmask:   "255.255.0.0"
                    local_mac: "00:98:28:28:14:00"

   for sriov/ovs_dpdk pod files, please refer above Standalone Virtualization for ovs-dpdk/sriov configuration

3. Start IxOS TCL Server (Install 'Ixia IxExplorer IxOS <version>')
   You will also need to configure the IxLoad machine to start the IXIA
   IxosTclServer. This can be started like so:
   Connect to the IxLoad machine using RDP
   Go to: Start->  Programs ->  Ixia ->   IxOS ->  IxOS 8.01-GA-Patch1  -> Ixia Tcl Server IxOS 8.01-GA-Patch1
          or "C:\Program Files (x86)\Ixia\IxOS\8.01-GA-Patch1\ixTclServer.exe"
4. Create a folder "Results" in c:\ and share the folder on the network.

5. execute testcase in samplevnf folder.
   eg <repo>/samples/vnf_ samples/nust/vfw/tc_baremetal_http_ixload_1b_Requests-65000_Concurrency.yaml

IxNetwork:
---------

Software required for IxNetwork
-----------------------------

1. Software needed : IxNetworkAPI<ixnetwork verson>Linux64.bin.tgz (Download from ixia support site)
                     Install - IxNetworkAPI<ixnetwork verson>Linux64.bin.tgz.
2. Update pod_ixia.yaml file with ixia details.
   cp <repo>/etc/yardstick/nodes/pod.yaml.nsb.sample.ixia etc/yardstick/nodes/pod_ixia.yaml

   Config pod_ixia.yaml
   ::

     nodes:
        -
            name: trafficgen_1
            role: IxNet
            ip: 1.2.1.1 #ixia machine ip
            user: user
            password: r00t
            key_filename: /root/.ssh/id_rsa
            tg_config:
                ixchassis: "1.2.1.7" #ixia chassis ip
                tcl_port: "8009" # tcl server port
                lib_path: "/opt/ixia/ixos-api/8.01.0.2/lib/ixTcl1.0"
                root_dir: "/opt/ixia/ixos-api/8.01.0.2/"
                py_bin_path: "/opt/ixia/ixload/8.01.106.3/bin/"
                py_lib_path: "/opt/ixia/ixnetwork/8.01.1029.14/lib/PythonApi"
                dut_result_dir: "/mnt/ixia"
                version: 8.1
            interfaces:
                xe0:  # logical name from topology.yaml and vnfd.yaml
                    vpci: "2:5" # Card:port
                    driver:    "none"
                    dpdk_port_num: 0
                    local_ip: "152.16.100.20"
                    netmask:   "255.255.0.0"
                    local_mac: "00:98:10:64:14:00"
                xe1:  # logical name from topology.yaml and vnfd.yaml
                    vpci: "2:6" # [(Card, port)]
                    driver:    "none"
                    dpdk_port_num: 1
                    local_ip: "152.40.40.20"
                    netmask:   "255.255.0.0"
                    local_mac: "00:98:28:28:14:00"

   for sriov/ovs_dpdk pod files, please refer above Standalone Virtualization for ovs-dpdk/sriov configuration

3. Start IxNetwork TCL Server
   You will also need to configure the IxNetwork machine to start the IXIA
   IxNetworkTclServer. This can be started like so:
   Connect to the IxNetwork machine using RDP
   Go to:     Start->  Programs ->  Ixia ->   IxNetwork ->   IxNetwork 7.21.893.14 GA ->   IxNetworkTclServer (or IxNetworkApiServer)

4. execute testcase in samplevnf folder.
   eg <repo>/samples/vnf_ samples/nust/vfw/tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml

Scale-up testcase:
==================

VNFs performance data with scale-up
* Helps to figure out optimal number of cores specification in the Virtual Machine template creation or VNF
* Helps in comparison between different VNF vendor offerings
* Better the scale-up index, indicates the performance scalability of a particular solution

1. Follow above traffic generator section to setup.
2. edit num of threads in <repo>/samples/vnf_samples/nust/vfw/tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_trex_scale_up.yaml
   ::

     e.g, 6 Threads  for given VNF
     schema: yardstick:task:0.1
     scenarios:
     {% for worker_thread in [1, 2 ,3 , 4, 5, 6] %}
     - type: NSPerf
       traffic_profile: ../../traffic_profiles/ipv4_throughput.yaml
       topology: vfw-tg-topology.yaml
       nodes:
         tg__0: trafficgen_1.yardstick
         vnf__0: vnf.yardstick
       options:
         framesize:
           uplink: {64B: 100}
           downlink: {64B: 100}
         flow:
           src_ip: [{'tg__0': 'xe0'}]
           dst_ip: [{'tg__0': 'xe1'}]
           count: 1
         traffic_type: 4
         rfc2544:
           allowed_drop_rate: 0.0001 - 0.0001
         vnf__0:
           rules: acl_1rule.yaml
           vnf_config: {lb_config: 'HW', lb_count: 1, worker_config: '1C/1T', worker_threads: {{worker_thread}}}
           nfvi_enable: True
       runner:
         type: Iteration
         iterations: 10
         interval: 35
     {% endfor %}
     context:
       type: Node
       name: yardstick
       nfvi_type: baremetal
       file: /etc/yardstick/nodes/pod.yaml

Scale-down testcase:
====================
VNFs performance data with scale-out
* Helps in capacity planning to meet the given network node requirements
* Helps in comparison between different VNF vendor offerings
* Better the scale-out index, provides the flexibility in meeting future capacity requirements


Scale-out not supported on Baremetal.

1. Follow above traffic generator section to setup.
2. Generate testcase for standalone virtualization using ansible scripts
   cd <repo>/ansible
   trex: standalone_ovs_scale_out_trex_test.yaml or standalone_sriov_scale_out_trex_test.yaml
   ixia: standalone_ovs_scale_out_ixia_test.yaml or standalone_sriov_scale_out_ixia_test.yaml
   ixia_correlated: standalone_ovs_scale_out_ixia_correlated_test.yaml or standalone_sriov_scale_out_ixia_correlated_test.yaml

   update the ovs_dpdk or sriov above ansible scripts reflect the setup
3. run the test
   <repo>/samples/vnf_samples/nust/tc_sriov_vfw_udp_ixia_correlated_scale_out-1.yaml
   <repo>/samples/vnf_samples/nust/tc_sriov_vfw_udp_ixia_correlated_scale_out-2.yaml
