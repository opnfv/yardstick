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

The VNFs require a clear L2 connect to the external network in order to
generate realistic traffic from multiple address ranges and ports.

In order to prevent Neutron from filtering traffic we have to disable Neutron
Port Security. We also disable DHCP on the data ports because we are binding
the ports to DPDK and do not need DHCP addresses.  We also disable gateways
because multiple default gateways can prevent SSH access to the VNF from the
floating IP.  We only want a gateway on the mgmt network

.. code-block:: yaml

    uplink_0:
      cidr: '10.1.0.0/24'
      gateway_ip: 'null'
      port_security_enabled: False
      enable_dhcp: 'false'

Heat Topologies
^^^^^^^^^^^^^^^

By default Heat will attach every node to every Neutron network that is
created. For scale-out tests we do not want to attach every node to every
network.

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


Availability zone
^^^^^^^^^^^^^^^^^

The configuration of the availability zone is requred in cases where location
of exact compute host/group of compute hosts needs to be specified for
:term:`SampleVNF` or traffic generator in the heat test case. If this is the
case, please follow the instructions below.

.. _`Create a host aggregate`:

1. Create a host aggregate in the OpenStack and add the available compute hosts
   into the aggregate group.

   .. note:: Change the ``<AZ_NAME>`` (availability zone name), ``<AGG_NAME>``
     (host aggregate name) and ``<HOST>`` (host name of one of the compute) in the
     commands below.

   .. code-block:: bash

     # create host aggregate
     openstack aggregate create --zone <AZ_NAME> \
       --property availability_zone=<AZ_NAME> <AGG_NAME>
     # show available hosts
     openstack compute service list --service nova-compute
     # add selected host into the host aggregate
     openstack aggregate add host <AGG_NAME> <HOST>

2. To specify the OpenStack location (the exact compute host or group of the hosts)
   of SampleVNF or traffic generator in the heat test case, the ``availability_zone`` server
   configuration option should be used. For example:

   .. note:: The ``<AZ_NAME>`` (availability zone name) should be changed according
     to the name used during the host aggregate creation steps above.

   .. code-block:: yaml

     context:
       name: yardstick
       image: yardstick-samplevnfs
       ...
       servers:
         vnf__0:
           ...
           availability_zone: <AZ_NAME>
           ...
         tg__0:
           ...
           availability_zone: <AZ_NAME>
           ...
       networks:
         ...

There are two example of SampleVNF scale out test case which use the
``availability zone`` feature to specify the exact location of scaled VNFs and
traffic generators.

Those are:

.. code-block:: console

  <repo>/samples/vnf_samples/nsut/prox/tc_prox_heat_context_l2fwd_multiflow-2-scale-out.yaml
  <repo>/samples/vnf_samples/nsut/vfw/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale_out.yaml

.. note:: This section describes the PROX scale-out testcase, but the same
  procedure is used for the vFW test case.

1. Before running the scale-out test case, make sure the host aggregates are
   configured in the OpenStack environment. To check this, run the following
   command:

   .. code-block:: console

     # show configured host aggregates (example)
     openstack aggregate list
     +----+------+-------------------+
     | ID | Name | Availability Zone |
     +----+------+-------------------+
     |  4 | agg0 | AZ_NAME_0         |
     |  5 | agg1 | AZ_NAME_1         |
     +----+------+-------------------+

2. If no host aggregates are configured, please follow the instructions to
   `Create a host aggregate`_


3. Run the SampleVNF PROX scale-out test case, specifying the
   ``availability zone`` of each VNF and traffic generator as task arguments.

   .. note:: The ``az_0`` and ``az_1`` should be changed according to the host
      aggregates created in the OpenStack.

   .. code-block:: console

     yardstick -d task start \
     <repo>/samples/vnf_samples/nsut/prox/tc_prox_heat_context_l2fwd_multiflow-2-scale-out.yaml\
       --task-args='{
         "num_vnfs": 4, "availability_zone": {
           "vnf_0": "az_0", "tg_0": "az_1",
           "vnf_1": "az_0", "tg_1": "az_1",
           "vnf_2": "az_0", "tg_2": "az_1",
           "vnf_3": "az_0", "tg_3": "az_1"
         }
       }'

   ``num_vnfs`` specifies how many VNFs are going to be deployed in the
   ``heat`` contexts. ``vnf_X`` and ``tg_X`` arguments configure the
   availability zone where the VNF and traffic generator is going to be deployed.


Collectd KPIs
-------------

NSB can collect KPIs from collected.  We have support for various plugins
enabled by the :term:`Barometer` project.

The default yardstick-samplevnf has collectd installed. This allows for
collecting KPIs from the VNF.

Collecting KPIs from the NFVi is more complicated and requires manual setup.
We assume that collectd is not installed on the compute nodes.

To collectd KPIs from the NFVi compute nodes:

    * install_collectd on the compute nodes
    * create pod.yaml for the compute nodes
    * enable specific plugins depending on the vswitch and DPDK

    example ``pod.yaml`` section for Compute node running collectd.

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
--------

VNFs performance data with scale-up

  * Helps to figure out optimal number of cores specification in the Virtual
    Machine template creation or VNF
  * Helps in comparison between different VNF vendor offerings
  * Better the scale-up index, indicates the performance scalability of a
    particular solution

Heat
^^^^
For VNF scale-up tests we increase the number for VNF worker threads.  In the
case of VNFs we also need to increase the number of VCPUs and memory allocated
to the VNF.

An example scale-up Heat testcase is:

.. literalinclude:: /../samples/vnf_samples/nsut/vfw/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale-up.yaml
   :language: yaml

This testcase template requires specifying the number of VCPUs, Memory and Ports.
We set the VCPUs and memory using the ``--task-args`` options

.. code-block:: console

  yardstick task start --task-args='{"mem": 10480, "vcpus": 4, "vports": 2}' \
  samples/vnf_samples/nsut/vfw/tc_heat_rfc2544_ipv4_1rule_1flow_64B_trex_scale-up.yaml

In order to support ports scale-up, traffic and topology templates need to be used in testcase.

A example topology template is:

.. literalinclude:: /../samples/vnf_samples/nsut/vfw/vfw-tg-topology-scale-up.yaml
   :language: yaml

This template has ``vports`` as an argument. To pass this argument it needs to
be configured in ``extra_args`` scenario definition. Please note that more
argument can be defined in that section. All of them will be passed to topology
and traffic profile templates

For example:

.. code-block:: yaml

   schema: yardstick:task:0.1
   scenarios:
   - type: NSPerf
     traffic_profile: ../../traffic_profiles/ipv4_throughput-scale-up.yaml
     extra_args:
       vports: {{ vports }}
     topology: vfw-tg-topology-scale-up.yaml

A example traffic profile template is:

.. literalinclude:: /../samples/vnf_samples/traffic_profiles/ipv4_throughput-scale-up.yaml
   :language: yaml

There is an option to provide predefined config for SampleVNFs. Path to config
file may by specified in ``vnf_config`` scenario section.

.. code-block:: yaml

   vnf__0:
      rules: acl_1rule.yaml
      vnf_config: {lb_config: 'SW', file: vfw_vnf_pipeline_cores_4_ports_2_lb_1_sw.conf }


Baremetal
^^^^^^^^^
  1. Follow above traffic generator section to setup.
  2. Edit num of threads in
     ``<repo>/samples/vnf_samples/nsut/vfw/tc_baremetal_rfc2544_ipv4_1rule_1flow_64B_trex_scale_up.yaml``
     e.g, 6 Threads for given VNF

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
---------

VNFs performance data with scale-out helps

  * capacity planning to meet the given network node requirements
  * comparison between different VNF vendor offerings
  * better the scale-out index, provides the flexibility in meeting future
    capacity requirements


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

There are sample scale-out all-VM Heat tests. These tests only use VMs and
don't use external traffic.

The tests use UDP_Replay and correlated traffic.

.. code-block:: console

  <repo>/samples/vnf_samples/nsut/cgnapt/tc_heat_rfc2544_ipv4_1flow_64B_trex_correlated_scale_4.yaml

To run the test you need to increase OpenStack CPU, Memory and Port quotas.


Traffic Generator tuning
------------------------

The TRex traffic generator can be setup to use multiple threads per core, this
is for multiqueue testing.

TRex does not automatically enable multiple threads because we currently cannot
detect the number of queues on a device.

To enable multiple queue set the ``queues_per_port`` value in the TG VNF
options section.

.. code-block:: yaml

  scenarios:
    - type: NSPerf
      nodes:
        tg__0: tg_0.yardstick

      options:
        tg_0:
          queues_per_port: 2


Standalone configuration
------------------------

NSB supports certain Standalone deployment configurations.
Standalone supports provisioning a VM in a standalone visualised environment using kvm/qemu.
There two types of Standalone contexts available: OVS-DPDK and SRIOV.
OVS-DPDK uses OVS network with DPDK drivers.
SRIOV enables network traffic to bypass the software switch layer of the Hyper-V stack.

Emulated machine type
^^^^^^^^^^^^^^^^^^^^^

For better performance test results of emulated VM spawned by Yardstick SA
context (OvS-DPDK/SRIOV), it may be important to control the emulated machine
type used by QEMU emulator. This attribute can be configured via TC definition
in ``contexts`` section under ``extra_specs`` configuration.

For example:

.. code-block:: yaml

  contexts:
     ...
     - type: StandaloneSriov
       ...
       flavor:
         ...
         extra_specs:
           ...
           machine_type: pc-i440fx-bionic

Where, ``machine_type`` can be set to one of the emulated machine type
supported by QEMU running on SUT platform. To get full list of supported
emulated machine types, the following command can be used on the target SUT
host.

.. code-block:: yaml

  # qemu-system-x86_64 -machine ?

By default, the ``machine_type`` option is set to ``pc-i440fx-xenial`` which is
suitable for running Ubuntu 16.04 VM image. So, if this type is not supported
by the target platform or another VM image is used for stand alone (SA) context
VM (e.g.: ``bionic`` image for Ubuntu 18.04), this configuration should be
changed accordingly.

Standalone with OVS-DPDK
^^^^^^^^^^^^^^^^^^^^^^^^

SampleVNF image is spawned in a VM on a baremetal server.
OVS with DPDK is installed on the baremetal server.

.. note:: Ubuntu 17.10 requires DPDK v.17.05 and higher, DPDK v.17.05 requires OVS v.2.8.0.

Default values for OVS-DPDK:

  * queues: 4
  * lcore_mask: ""
  * pmd_cpu_mask: "0x6"

Sample test case file
^^^^^^^^^^^^^^^^^^^^^

1. Prepare SampleVNF image and copy it to ``flavor/images``.
2. Prepare context files for TREX and SampleVNF under ``contexts/file``.
3. Add bridge named ``br-int`` to the baremetal where SampleVNF image is deployed.
4. Modify ``networks/phy_port`` accordingly to the baremetal setup.
5. Run test from:

.. literalinclude:: /../samples/vnf_samples/nsut/acl/tc_ovs_rfc2544_ipv4_1rule_1flow_64B_trex.yaml
   :language: yaml

Preparing test run of vEPC test case
------------------------------------

Provided vEPC test cases are examples of emulation of vEPC infrastructure
components, such as UE, eNodeB, MME, SGW, PGW.

Location of vEPC test cases: ``samples/vnf_samples/nsut/vepc/``.

Before running a specific vEPC test case using NSB, some preconfiguration
needs to be done.

Update Spirent Landslide TG configuration in pod file
=====================================================

Examples of ``pod.yaml`` files could be found in
:file:`etc/yardstick/nodes/standalone`.
The name of related pod file could be checked in the context section of NSB
test case.

The ``pod.yaml`` related to vEPC test case uses some sub-structures that hold the
details of accessing the Spirent Landslide traffic generator.
These subsections and the changes to be done in provided example pod file are
described below.

1. ``tas_manager``: data under this key holds the information required to
access Landslide TAS (Test Administration Server) and perform needed
configurations on it.

 * ``ip``: IP address of TAS Manager node; should be updated according to test
   setup used
 * ``super_user``: superuser name; could be retrieved from Landslide documentation
 * ``super_user_password``: superuser password; could be retrieved from
   Landslide documentation
 * ``cfguser_password``: password of predefined user named 'cfguser'; default
   password could be retrieved from Landslide documentation
 * ``test_user``: username to be used during test run as a Landslide library
   name; to be defined by test run operator
 * ``test_user_password``: password of test user; to be defined by test run
   operator
 * ``proto``: *http* or *https*; to be defined by test run operator
 * ``license``: Landslide license number installed on TAS

2. The ``config`` section holds information about test servers (TSs) and
systems under test (SUTs). Data is represented as a list of entries.
Each such entry contains:

 * ``test_server``: this subsection represents data related to test server
   configuration, such as:

   * ``name``: test server name; unique custom name to be defined by test
     operator
   * ``role``: this value is used as a key to bind specific Test Server and
     TestCase; should be set to one of test types supported by TAS license
   * ``ip``: Test Server IP address
   * ``thread_model``: parameter related to Test Server performance mode.
     The value should be one of the following: "Legacy" | "Max" | "Fireball".
     Refer to Landslide documentation for details.
   * ``phySubnets``: a structure used to specify IP ranges reservations on
     specific network interfaces of related Test Server. Structure fields are:

    * ``base``: start of IP address range
    * ``mask``: IP range mask in CIDR format
    * ``name``: network interface name, e.g. *eth1*
    * ``numIps``: size of IP address range

 * ``preResolvedArpAddress``: a structure used to specify the range of IP
   addresses for which the ARP responses will be emulated

    * ``StartingAddress``: IP address specifying the start of IP address range
    * ``NumNodes``: size of the IP address range

 * ``suts``: a structure that contains definitions of each specific SUT
   (represents a vEPC component). SUT structure contains following key/value
   pairs:

    * ``name``: unique custom string specifying SUT name
    * ``role``: string value corresponding with an SUT role specified in the
      session profile (test session template) file
    * ``managementIp``: SUT management IP adress
    * ``phy``: network interface name, e.g. *eth1*
    * ``ip``: vEPC component IP address used in test case topology
    * ``nextHop``: next hop IP address, to allow for vEPC inter-node communication

Update NSB test case definitions
================================
NSB test case file designated for vEPC testing contains an example of specific
test scenario configuration.
Test operator may change these definitions as required for the use case that
requires testing.
Specifically, following subsections of the vEPC test case (section **scenarios**)
may be changed.

1. Subsection ``options``: contains custom parameters used for vEPC testing

 * subsection ``dmf``: may contain one or more parameters specified in
   ``traffic_profile`` template file
 * subsection ``test_cases``: contains re-definitions of parameters specified
   in ``session_profile`` template file

    .. note:: All parameters in ``session_profile``, value of which is a
      placeholder, needs to be re-defined to construct a valid test session.

2. Subsection ``runner``: specifies the test duration and the interval of
TG and VNF side KPIs polling. For more details, refer to :doc:`03-architecture`.

Preparing test run of vPE test case
-----------------------------------
The vPE (Provider Edge Router) is a :term: `VNF` approximation
serving as an Edge Router. The vPE is approximated using the
``ip_pipeline`` dpdk application.

         .. image:: images/vPE_Diagram.png
            :width: 800px
            :alt: NSB vPE Diagram

The ``vpe_config`` file must be passed as it is not auto generated.
The ``vpe_script`` defines the rules applied to each of the pipelines. This can be
auto generated or a file can be passed using the ``script_file`` option in
``vnf_config`` as shown below. The ``full_tm_profile_file`` option must be
used if a traffic manager is defined in ``vpe_config``.

.. code-block:: yaml

     vnf_config: { file: './vpe_config/vpe_config_2_ports',
                   action_bulk_file: './vpe_config/action_bulk_512.txt',
                   full_tm_profile_file: './vpe_config/full_tm_profile_10G.cfg',
                   script_file: './vpe_config/vpe_script_sample' }

Testcases for vPE can be found in the ``vnf_samples/nsut/vpe`` directory.
A testcase can be started with the following command as an example:

.. code-block:: bash

    yardstick task start /yardstick/samples/vnf_samples/nsut/vpe/tc_baremetal_rfc2544_ipv4_1flow_64B_ixia.yaml

Preparing test run of vIPSEC test case
------------------------------------

Location of vIPSEC test cases: ``samples/vnf_samples/nsut/ipsec/``.

Before running a specific vIPSEC test case using NSB, some dependencies have to be preinstalled and properly configured.
- VPP

    | ``$ export UBUNTU="xenial"``
    | ``$ export RELEASE=".stable.1810"``
    | ``$ sudo rm /etc/apt/sources.list.d/99fd.io.list``
    | ``$ echo "deb [trusted=yes] https://nexus.fd.io/content/repositories/fd.io$RELEASE.ubuntu.$UBUNTU.main/ ./" | sudo tee -a /etc/apt/sources.list.d/99fd.io.list``
    | ``$ sudo apt-get update``
    | ``$ sudo apt-get install vpp vpp-lib vpp-plugin vpp-dbg vpp-dev vpp-api-java vpp-api-python vpp-api-lua``

- VAT templates

    VAT templates is required for the VPP API.

    ```sh
    mkdir -p /opt/nsb_bin/vpp/templates/
    echo 'exec trace add dpdk-input 50' > /opt/nsb_bin/vpp/templates/enable_dpdk_traces.vat
    echo 'exec trace add vhost-user-input 50' > /opt/nsb_bin/vpp/templates/enable_vhost_user_traces.vat
    echo 'exec trace add memif-input 50' > /opt/nsb_bin/vpp/templates/enable_memif_traces.vat
    cat > /opt/nsb_bin/vpp/templates/dump_interfaces.vat << EOL
    sw_interface_dump
    dump_interface_table
    quit
    EOL

    ```
