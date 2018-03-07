.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, 2016-2017 Intel Corporation.

Yardstick - NSB Testing - Operation
===================================

Abstract
--------

NSB test configuration and OpenStack setup requirements


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
DHCP addresses.  We also disable gateways because multiple default gateways can prevent SSH access
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

In this example we have ``TRex xe0 <-> xe0 VNF xe1 <-> xe0 UDP_Replay``

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

Collectd KPIs
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



Scale-Up
------------------

VNFs performance data with scale-up

  * Helps to figure out optimal number of cores specification in the Virtual Machine template creation or VNF
  * Helps in comparison between different VNF vendor offerings
  * Better the scale-up index, indicates the performance scalability of a particular solution

Heat
^^^^

For VNF scale-up tests we increase the number for VNF worker threads.  In the case of VNFs
we also need to increase the number of VCPUs and memory allocated to the VNF.

An example scale-up Heat testcase is:

.. code-block:: console

  <repo>/samples/vnf_samples/nsut/acl/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale_up.yaml

This testcase template requires specifying the number of VCPUs and Memory.
We set the VCPUs and memory using the --task-args options

.. code-block:: console

  yardstick --debug task start --task-args='{"mem": 20480, "vcpus": 10}'   samples/vnf_samples/nsut/acl/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale_up.yaml


Baremetal
^^^^^^^^^
  1. Follow above traffic generator section to setup.
  2. edit num of threads in ``<repo>/samples/vnf_samples/nsut/vfw/tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_trex_scale_up.yaml``

  e.g, 6 Threads  for given VNF

.. code-block:: yaml


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

Scale-Out
--------------------

VNFs performance data with scale-out

  * Helps in capacity planning to meet the given network node requirements
  * Helps in comparison between different VNF vendor offerings
  * Better the scale-out index, provides the flexibility in meeting future capacity requirements


Standalone
^^^^^^^^^^

Scale-out not supported on Baremetal.

1. Follow above traffic generator section to setup.
2. Generate testcase for standalone virtualization using ansible scripts

  .. code-block:: console

    cd <repo>/ansible
    trex: standalone_ovs_scale_out_trex_test.yaml or standalone_sriov_scale_out_trex_test.yaml
    ixia: standalone_ovs_scale_out_ixia_test.yaml or standalone_sriov_scale_out_ixia_test.yaml
    ixia_correlated: standalone_ovs_scale_out_ixia_correlated_test.yaml or standalone_sriov_scale_out_ixia_correlated_test.yaml

  update the ovs_dpdk or sriov above Ansible scripts reflect the setup

3. run the test

  .. code-block:: console

    <repo>/samples/vnf_samples/nsut/tc_sriov_vfw_udp_ixia_correlated_scale_out-1.yaml
    <repo>/samples/vnf_samples/nsut/tc_sriov_vfw_udp_ixia_correlated_scale_out-2.yaml

Heat
^^^^

There are sample scale-out all-VM Heat tests.  These tests only use VMs and don't use external traffic.

The tests use UDP_Replay and correlated traffic.

.. code-block:: console

  <repo>/samples/vnf_samples/nsut/cgnapt/tc_heat_rfc2544_ipv4_1flow_64B_trex_correlated_scale_4.yaml

To run the test you need to increase OpenStack CPU, Memory and Port quotas.


Traffic Generator tuning
------------------------

The TRex traffic generator can be setup to use multiple threads per core, this is for multiqueue testing.

TRex does not automatically enable multiple threads because we currently cannot detect the number of queues on a device.

To enable multiple queue set the queues_per_port value in the TG VNF options section.

.. code-block:: yaml

  scenarios:
    - type: NSPerf
      nodes:
        tg__0: tg_0.yardstick

      options:
        tg_0:
          queues_per_port: 2


