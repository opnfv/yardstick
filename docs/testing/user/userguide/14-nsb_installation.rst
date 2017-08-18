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

Refer chapter :doc:`04-installation` for more information on installing *Yardstick*

After *Yardstick* is installed, executing the "nsb_setup.sh" script to setup
NSB testing.

::

  ./nsb_setup.sh

It will also automatically download all the packages needed for NSB Testing setup.

System Topology:
-----------------

.. code-block:: console

  +----------+              +----------+
  |          |              |          |
  |          | (0)----->(0) |   Ping/  |
  |    TG1   |              |   vPE/   |
  |          |              |   2Trex  |
  |          | (1)<-----(1) |          |
  +----------+              +----------+
  trafficgen_1                   vnf


OpenStack parameters and credentials
------------------------------------

Environment variables
^^^^^^^^^^^^^^^^^^^^^

Before running Yardstick (NSB Testing) it is necessary to export traffic
generator libraries.

::

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


Config pod.yaml describing Topology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before executing Yardstick test cases, make sure that pod.yaml reflects the
topology and update all the required fields.

::

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
python virtual environment

::

    source /opt/nsb_bin/yardstick_venv/bin/activate


Run Yardstick - Network Service Testcases
-----------------------------------------

NS testing - using NSBperf CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /opt/nsb_setup/yardstick_venv/bin/activate
  PYTHONPATH: ". ~/.bash_profile"
  cd <yardstick_repo>/yardstick/cmd

 Execute command: ./NSPerf.py -h
      ./NSBperf.py --vnf <selected vnf> --test <rfc test>
      eg: ./NSBperf.py --vnf vpe --test tc_baremetal_rfc2544_ipv4_1flow_64B.yaml

NS testing - using yardstick CLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /opt/nsb_setup/yardstick_venv/bin/activate
  PYTHONPATH: ". ~/.bash_profile"

Go to test case forlder type we want to execute.
      e.g. <yardstick repo>/samples/vnf_samples/nsut/<vnf>/
      run: yardstick --debug task start <test_case.yaml>
