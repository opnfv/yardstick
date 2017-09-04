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

Prerequisite preparation::

  apt-get update && apt-get install -y git python-setuptools python-pip
  easy_install -U setuptools==30.0.0
  pip install appdirs==1.4.0
  pip install virtualenv

Create a virtual environment::

  virtualenv ~/yardstick_venv
  export YARDSTICK_VENV=~/yardstick_venv
  source ~/yardstick_venv/bin/activate

Download the source code and install Yardstick from it::

  git clone https://gerrit.opnfv.org/gerrit/yardstick
  export YARDSTICK_REPO_DIR=~/yardstick
  cd yardstick
  ./install.sh


After *Yardstick* is installed, executing the "nsb_setup.sh" script to setup
NSB testing::

  ./nsb_setup.sh

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

Enable yardstick virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before executing yardstick test cases, make sure to activate yardstick
python virtual environment if runnin on ubuntu without docker::

    source /opt/nsb_bin/yardstick_venv/bin/activate

On docker, virtual env is in main path.

Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  PYTHONPATH: ". ~/.bash_profile"
  cd <yardstick_repo>/yardstick/cmd

 Execute command: ./NSPerf.py -h
      ./NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./NSBperf.py --vnf vpe --test tc_baremetal_rfc2544_ipv4_1flow_64B.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. <yardstick repo>/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>

Network Service Benchmarking - Standalone Virtualization 
-----------------------------------------

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

    Also you may need install several additional packages to use this tool, by
    follwing the commands below::

       sudo apt-get update && sudo apt-get install -y qemu-utils kpartx

    This image can be built using the following command in the directory where Yardstick is installed::

       export YARD_IMG_ARCH='amd64'
       sudo echo "Defaults env_keep += \'YARD_IMG_ARCH\'" >> /etc/sudoers
       sudo tools/yardstick-img-dpdk-modify tools/ubuntu-server-cloudimg-samplevnf-modify.sh

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

    cp /etc/yardstick/nodes/pod.yaml.nsb.sriov.sample /etc/yardstick/nodes/pod.yaml

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
    name: sriov
    role: Sriov
    ip: 2.2.2.2
    user: root
    auth_type: password
    password: password
    vf_macs:
     - "00:00:00:00:00:03"
     - "00:00:00:00:00:04"
    phy_ports: # Physical ports to configure sriov
     - "0000:06:00.0"
     - "0000:06:00.1"
    phy_driver:    i40e # kernel driver
    images: "/var/lib/libvirt/images/ubuntu1.img"

    -
        name: vnf
        role: vnf
        ip: 1.1.1.2
        user: root
        password: r00t
        host: 2.2.2.2 #BM - host == ip, virtualized env - Host - compute node
        interfaces:
            xe0:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:00:07.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 0
                local_ip: "152.16.100.10"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:03"

            xe1:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:00:08.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 1
                local_ip: "152.16.40.10"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:04"
        routing_table:
        - network: "152.16.100.10"
          netmask: "255.255.255.0"
          gateway: "152.16.100.20"
          if: "xe0"
        - network: "152.16.40.10"
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

Enable yardstick virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before executing yardstick test cases, make sure to activate yardstick
python virtual environment if runnin on ubuntu without docker::

    source /opt/nsb_bin/yardstick_venv/bin/activate

On docker, virtual env is in main path.

Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  PYTHONPATH: ". ~/.bash_profile"
  cd <yardstick_repo>/yardstick/cmd

 Execute command: ./NSPerf.py -h
      ./NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./NSBperf.py --vnf vfw --test tc_sriov_rfc2544_ipv4_1flow_64B.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. <yardstick repo>/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>

OVS-DPDK:
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

    Also you may need install several additional packages to use this tool, by
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
topology and update all the required fields.::

    cp /etc/yardstick/nodes/pod.yaml.nsb.sriov.sample /etc/yardstick/nodes/pod.yaml

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
    name: sriov
    role: Sriov
    ip: 2.2.2.2
    user: root
    auth_type: password
    password: password
    vpath: "/usr/local/"
    vports:
     - dpdkvhostuser0
     - dpdkvhostuser1
    vports_mac:
     - "00:00:00:00:00:03"
     - "00:00:00:00:00:04"
    phy_ports: # Physical ports to configure ovs
     - "0000:06:00.0"
     - "0000:06:00.1"
    flow:
     - ovs-ofctl add-flow br0 in_port=1,action=output:3
     - ovs-ofctl add-flow br0 in_port=3,action=output:1
     - ovs-ofctl add-flow br0 in_port=4,action=output:2
     - ovs-ofctl add-flow br0 in_port=2,action=output:4
    phy_driver:    i40e # kernel driver
    images: "/var/lib/libvirt/images/ubuntu1.img"

    -
        name: vnf
        role: vnf
        ip: 1.1.1.2
        user: root
        password: r00t
        host: 2.2.2.2 #BM - host == ip, virtualized env - Host - compute node
        interfaces:
            xe0:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:00:04.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 0
                local_ip: "152.16.100.10"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:03"

            xe1:  # logical name from topology.yaml and vnfd.yaml
                vpci:      "0000:00:05.0"
                driver:    i40e # default kernel driver
                dpdk_port_num: 1
                local_ip: "152.16.40.10"
                netmask:   "255.255.255.0"
                local_mac: "00:00:00:00:00:04"
        routing_table:
        - network: "152.16.100.10"
          netmask: "255.255.255.0"
          gateway: "152.16.100.20"
          if: "xe0"
        - network: "152.16.40.10"
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

Enable yardstick virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before executing yardstick test cases, make sure to activate yardstick
python virtual environment if runnin on ubuntu without docker::

    source /opt/nsb_bin/yardstick_venv/bin/activate

On docker, virtual env is in main path.

Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  PYTHONPATH: ". ~/.bash_profile"
  cd <yardstick_repo>/yardstick/cmd

 Execute command: ./NSPerf.py -h
      ./NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./NSBperf.py --vnf vfw --test tc_sriov_rfc2544_ipv4_1flow_64B.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::
  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. <yardstick repo>/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>
