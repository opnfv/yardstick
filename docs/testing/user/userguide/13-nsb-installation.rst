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
* Setup/Reference pod.yaml describing Test topology
* Create/Reference the test configuration yaml file.
* Run the test case.


Prerequisites
-------------

Refer chapter Yardstick Installation for more information on yardstick
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


   +-----------+--------------------+
   | Item      | Description        |
   +-----------+--------------------+
   | Memory    | Min 20GB           |
   +-----------+--------------------+
   | NICs      | 2 x 10G            |
   +-----------+--------------------+
   | OS        | Ubuntu 16.04.3 LTS |
   +-----------+--------------------+
   | kernel    | 4.4.0-34-generic   |
   +-----------+--------------------+
   | DPDK      | 17.02              |
   +-----------+--------------------+

Boot and BIOS settings:


   +------------------+---------------------------------------------------+
   | Boot settings    | default_hugepagesz=1G hugepagesz=1G hugepages=16  |
   |                  | hugepagesz=2M hugepages=2048 isolcpus=1-11,22-33  |
   |                  | nohz_full=1-11,22-33 rcu_nocbs=1-11,22-33         |
   |                  | iommu=on iommu=pt intel_iommu=on                  |
   |                  | Note: nohz_full and rcu_nocbs is to disable Linux |
   |                  | kernel interrupts                                 |
   +------------------+---------------------------------------------------+
   |BIOS              | CPU Power and Performance Policy <Performance>    |
   |                  | CPU C-state Disabled                              |
   |                  | CPU P-state Disabled                              |
   |                  | Enhanced Intel® Speedstep® Tech Disabled          |
   |                  | Hyper-Threading Technology (If supported) Enabled |
   |                  | Virtualization Techology Enabled                  |
   |                  | Intel(R) VT for Direct I/O Enabled                |
   |                  | Coherency Enabled                                 |
   |                  | Turbo Boost Disabled                              |
   +------------------+---------------------------------------------------+



Install Yardstick (NSB Testing)
-------------------------------

Download the source code and install Yardstick from it

.. code-block:: console

  git clone https://gerrit.opnfv.org/gerrit/yardstick

  cd yardstick

  # Switch to latest stable branch
  # git checkout <tag or stable branch>
  git checkout stable/euphrates

Configure the network proxy, either using the environment variables or setting
the global environment file:

.. code-block:: ini
    cat /etc/environment
    http_proxy='http://proxy.company.com:port'
    https_proxy='http://proxy.company.com:port'

.. code-block:: console
    export http_proxy='http://proxy.company.com:port'
    export https_proxy='http://proxy.company.com:port'

The last step is to modify the Yardstick installation inventory, used by
Ansible:

.. code-block:: ini
  cat ./ansible/yardstick-install-inventory.ini
  [jumphost]
  localhost  ansible_connection=local

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


To execute an installation for a Bare-Metal or a Standalone context:

.. code-block:: console

    ./nsb_setup.sh


To execute an installation for an OpenStack context:

.. code-block:: console

    ./nsb_setup.sh <path to admin-openrc.sh>

Above command setup docker with latest yardstick code. To execute

.. code-block:: console

  docker exec -it yardstick bash

It will also automatically download all the packages needed for NSB Testing setup.
Refer chapter :doc:`04-installation` for more on docker **Install Yardstick using Docker (recommended)**

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


Environment parameters and credentials
--------------------------------------

Config yardstick conf
^^^^^^^^^^^^^^^^^^^^^

If user did not run 'yardstick env influxdb' inside the container, which will generate
correct yardstick.conf, then create the config file manually (run inside the container):

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

Run Yardstick - Network Service Testcases
-----------------------------------------


NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  See :doc:`04-installation`

.. code-block:: console


  docker exec -it yardstick /bin/bash
  source /etc/yardstick/openstack.creds (only for heat TC if nsb_setup.sh was NOT used)
  export EXTERNAL_NETWORK="<openstack public network>" (only for heat TC)
  yardstick --debug task start yardstick/samples/vnf_samples/nsut/<vnf>/<test case>

Network Service Benchmarking - Bare-Metal
-----------------------------------------

Bare-Metal Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bare-Metal 2-Node setup:
########################
.. code-block:: console

  +----------+              +----------+
  |          |              |          |
  |          | (0)----->(0) |          |
  |    TG1   |              |    DUT   |
  |          |              |          |
  |          | (n)<-----(n) |          |
  +----------+              +----------+
  trafficgen_1                   vnf

Bare-Metal 3-Node setup - Correlated Traffic:
#############################################
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
Before executing Yardstick test cases, make sure that pod.yaml reflects the
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


Network Service Benchmarking - Standalone Virtualization
--------------------------------------------------------

SR-IOV:
^^^^^^^

SR-IOV Pre-requisites
#####################

On Host:
 a) Create a bridge for VM to connect to external network

  .. code-block:: console

      brctl addbr br-int
      brctl addif br-int <interface_name>    #This interface is connected to internet

 b) Build guest image for VNF to run.
    Most of the sample test cases in Yardstick are using a guest image called
    ``yardstick-image`` which deviates from an Ubuntu Cloud Server image
    Yardstick has a tool for building this custom image with samplevnf.
    It is necessary to have ``sudo`` rights to use this tool.

    Also you may need to install several additional packages to use this tool, by
    following the commands below::

       sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

    This image can be built using the following command in the directory where Yardstick is installed

    .. code-block:: console

       export YARD_IMG_ARCH='amd64'
       sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers

    Please use ansible script to generate a cloud image refer to :doc:`04-installation`

    for more details refer to chapter :doc:`04-installation`

    .. note:: VM should be build with static IP and should be accessible from yardstick host.


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

.. code-block:: console

    cp <yardstick>/etc/yardstick/nodes/standalone/trex_bm.yaml.sample /etc/yardstick/nodes/standalone/pod_trex.yaml
    cp <yardstick>/etc/yardstick/nodes/standalone/host_sriov.yaml /etc/yardstick/nodes/standalone/host_sriov.yaml

.. note:: Update all the required fields like ip, user, password, pcis, etc...

SR-IOV Config pod_trex.yaml
###########################

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
#############################

.. code-block:: YAML

    nodes:
    -
       name: sriov
       role: Sriov
       ip: 192.168.100.101
       user: ""
       password: ""

SR-IOV testcase update: ``<yardstick>/samples/vnf_samples/nsut/vfw/tc_sriov_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``

Update "contexts" section
"""""""""""""""""""""""""

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



OVS-DPDK:
^^^^^^^^^

OVS-DPDK Pre-requisites
#######################

On Host:
 a) Create a bridge for VM to connect to external network

  .. code-block:: console

      brctl addbr br-int
      brctl addif br-int <interface_name>    #This interface is connected to internet

 b) Build guest image for VNF to run.
    Most of the sample test cases in Yardstick are using a guest image called
    ``yardstick-image`` which deviates from an Ubuntu Cloud Server image
    Yardstick has a tool for building this custom image with samplevnf.
    It is necessary to have ``sudo`` rights to use this tool.

    Also you may need to install several additional packages to use this tool, by
    following the commands below::

       sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

    This image can be built using the following command in the directory where Yardstick is installed::

       export YARD_IMG_ARCH='amd64'
       sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers
       sudo tools/yardstick-img-dpdk-modify tools/ubuntu-server-cloudimg-samplevnf-modify.sh

    for more details refer to chapter :doc:`04-installation`

    .. note::  VM should be build with static IP and should be accessible from yardstick host.

 c) OVS & DPDK version.
     - OVS 2.7 and DPDK 16.11.1 above version is supported

 d) Setup OVS/DPDK on host.
     Please refer to below link on how to setup `OVS-DPDK <http://docs.openvswitch.org/en/latest/intro/install/dpdk/>`_


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

.. code-block:: console

  cp <yardstick>/etc/yardstick/nodes/standalone/trex_bm.yaml.sample /etc/yardstick/nodes/standalone/pod_trex.yaml
  cp <yardstick>/etc/yardstick/nodes/standalone/host_ovs.yaml /etc/yardstick/nodes/standalone/host_ovs.yaml

.. note:: Update all the required fields like ip, user, password, pcis, etc...

OVS-DPDK Config pod_trex.yaml
#############################

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
#############################

.. code-block:: YAML

    nodes:
    -
       name: ovs_dpdk
       role: OvsDpdk
       ip: 192.168.100.101
       user: ""
       password: ""

ovs_dpdk testcase update: ``<yardstick>/samples/vnf_samples/nsut/vfw/tc_ovs_rfc2544_ipv4_1rule_1flow_64B_trex.yaml``

Update "contexts" section
"""""""""""""""""""""""""

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


Enabling other Traffic generator
--------------------------------

IxLoad:
^^^^^^^

1. Software needed: IxLoadAPI ``<IxLoadTclApi verson>Linux64.bin.tgz and <IxOS version>Linux64.bin.tar.gz`` (Download from ixia support site)
                     Install - ``<IxLoadTclApi verson>Linux64.bin.tgz & <IxOS version>Linux64.bin.tar.gz``
   If the installation was not done inside the container, after installing the IXIA client,
   check /opt/ixia/ixload/<ver>/bin/ixloadpython and make sure you can run this cmd
   inside the yardstick container. Usually user is required to copy or link /opt/ixia/python/<ver>/bin/ixiapython
   to /usr/bin/ixiapython<ver> inside the container.

2. Update pod_ixia.yaml file with ixia details.

  .. code-block:: console

    cp <repo>/etc/yardstick/nodes/pod.yaml.nsb.sample.ixia etc/yardstick/nodes/pod_ixia.yaml

  Config pod_ixia.yaml

  .. code-block:: yaml


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

  for sriov/ovs_dpdk pod files, please refer to above Standalone Virtualization for ovs-dpdk/sriov configuration

3. Start IxOS TCL Server (Install 'Ixia IxExplorer IxOS <version>')
   You will also need to configure the IxLoad machine to start the IXIA
   IxosTclServer. This can be started like so:

   - Connect to the IxLoad machine using RDP
   - Go to:
    ``Start->Programs->Ixia->IxOS->IxOS 8.01-GA-Patch1->Ixia Tcl Server IxOS 8.01-GA-Patch1``
     or
    ``"C:\Program Files (x86)\Ixia\IxOS\8.01-GA-Patch1\ixTclServer.exe"``

4. Create a folder "Results" in c:\ and share the folder on the network.

5. execute testcase in samplevnf folder.
   eg ``<repo>/samples/vnf_samples/nsut/vfw/tc_baremetal_http_ixload_1b_Requests-65000_Concurrency.yaml``

IxNetwork:
^^^^^^^^^^

1. Software needed: ``IxNetworkAPI<ixnetwork verson>Linux64.bin.tgz`` (Download from ixia support site)
                     Install - ``IxNetworkAPI<ixnetwork verson>Linux64.bin.tgz``
2. Update pod_ixia.yaml file with ixia details.

  .. code-block:: console

    cp <repo>/etc/yardstick/nodes/pod.yaml.nsb.sample.ixia etc/yardstick/nodes/pod_ixia.yaml

  Config pod_ixia.yaml

  .. code-block:: yaml

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

  for sriov/ovs_dpdk pod files, please refer to above Standalone Virtualization for ovs-dpdk/sriov configuration

3. Start IxNetwork TCL Server
   You will also need to configure the IxNetwork machine to start the IXIA
   IxNetworkTclServer. This can be started like so:

    - Connect to the IxNetwork machine using RDP
    - Go to:     ``Start->Programs->Ixia->IxNetwork->IxNetwork 7.21.893.14 GA->IxNetworkTclServer`` (or ``IxNetworkApiServer``)

4. execute testcase in samplevnf folder.
   eg ``<repo>/samples/vnf_samples/nsut/vfw/tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_ixia.yaml``

