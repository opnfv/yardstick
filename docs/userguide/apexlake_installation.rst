.. This work is licensed under a Creative Commons Attribution 4.0 International
.. License.
.. http://creativecommons.org/licenses/by/4.0
.. (c) OPNFV, Intel Corporation and others.


.. _DPDK: http://dpdk.org/doc/nics
.. _DPDK-pktgen: https://github.com/Pktgen/Pktgen-DPDK/
.. _SRIOV: https://wiki.openstack.org/wiki/SR-IOV-Passthrough-For-Networking
.. _PORTSEC: https://wiki.openstack.org/wiki/Neutron/ML2PortSecurityExtensionDriver
.. _here: https://wiki.opnfv.org/vtc


============================
Apexlake Installation Guide
============================

Abstract
--------

ApexLake is a framework that provides automatic execution of experiments and
related data collection to enable a user validate infrastructure from the
perspective of a Virtual Network Function (:term:`VNF`).

In the context of Yardstick, a virtual Traffic Classifier (:term:`VTC`) network
function is utilized.


Framework Hardware Dependencies
===============================

In order to run the framework there are some hardware related dependencies for
ApexLake.

The framework needs to be installed on the same physical node where DPDK-pktgen_
is installed.

The installation requires the physical node hosting the packet generator must
have 2 NICs which are DPDK_ compatible.

The 2 NICs will be connected to the switch where the OpenStack VM
network is managed.

The switch used must support multicast traffic and :term:`IGMP` snooping.
Further details about the configuration are provided at the following here_.

The corresponding ports to which the cables are connected need to be configured
as VLAN trunks using two of the VLAN IDs available for Neutron.
Note the VLAN IDs used as they will be required in later configuration steps.


Framework Software Dependencies
===============================
Before starting the framework, a number of dependencies must first be installed.
The following describes the set of instructions to be executed via the Linux
shell in order to install and configure the required dependencies.

1. Install Dependencies.

To support the framework dependencies the following packages must be installed.
The example provided is based on Ubuntu and needs to be executed in root mode.

::

    apt-get install python-dev
    apt-get install python-pip
    apt-get install python-mock
    apt-get install tcpreplay
    apt-get install libpcap-dev

2. Source OpenStack openrc file.

::

    source openrc

3. Configure Openstack Neutron

In order to support traffic generation and management by the virtual
Traffic Classifier, the configuration of the port security driver
extension is required for Neutron.

For further details please follow the following link: PORTSEC_
This step can be skipped in case the target OpenStack is Juno or Kilo release,
but it is required to support Liberty.
It is therefore required to indicate the release version in the configuration
file located in ./yardstick/vTC/apexlake/apexlake.conf


4. Create Two Networks based on VLANs in Neutron.

To enable network communications between the packet generator and the compute
node, two networks must be created via Neutron and mapped to the VLAN IDs
that were previously used in the configuration of the physical switch.
The following shows the typical set of commands required to configure Neutron
correctly.
The physical switches need to be configured accordingly.

::

    VLAN_1=2032
    VLAN_2=2033
    PHYSNET=physnet2
    neutron net-create apexlake_inbound_network \
            --provider:network_type vlan \
            --provider:segmentation_id $VLAN_1 \
            --provider:physical_network $PHYSNET

    neutron subnet-create apexlake_inbound_network \
            192.168.0.0/24 --name apexlake_inbound_subnet

    neutron net-create apexlake_outbound_network \
            --provider:network_type vlan \
            --provider:segmentation_id $VLAN_2 \
            --provider:physical_network $PHYSNET

    neutron subnet-create apexlake_outbound_network 192.168.1.0/24 \
            --name apexlake_outbound_subnet


5. Download Ubuntu Cloud Image and load it on Glance

The virtual Traffic Classifier is supported on top of Ubuntu 14.04 cloud image.
The image can be downloaded on the local machine and loaded on Glance
using the following commands:

::

    wget cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img
    glance image-create \
            --name ubuntu1404 \
            --is-public true \
            --disk-format qcow \
            --container-format bare \
            --file trusty-server-cloudimg-amd64-disk1.img



6. Configure the Test Cases

The VLAN tags must also be included in the test case Yardstick yaml file
as parameters for the following test cases:

    * :doc:`opnfv_yardstick_tc006`

    * :doc:`opnfv_yardstick_tc007`

    * :doc:`opnfv_yardstick_tc020`

    * :doc:`opnfv_yardstick_tc021`


Install and Configure DPDK Pktgen
+++++++++++++++++++++++++++++++++

Execution of the framework is based on DPDK Pktgen.
If DPDK Pktgen has not installed, it is necessary to download, install, compile
and configure it.
The user can create a directory and download the dpdk packet generator source
code:

::

    cd experimental_framework/libraries
    mkdir dpdk_pktgen
    git clone https://github.com/pktgen/Pktgen-DPDK.git

For instructions on the installation and configuration of DPDK and DPDK Pktgen
please follow the official DPDK Pktgen README file.
Once the installation is completed, it is necessary to load the DPDK kernel
driver, as follow:

::

    insmod uio
    insmod DPDK_DIR/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko

It is necessary to set the configuration file  to support the desired Pktgen
configuration.
A description of the required configuration parameters and supporting examples
is provided in the following:

::

    [PacketGen]
    packet_generator = dpdk_pktgen

    # This is the directory where the packet generator is installed
    # (if the user previously installed dpdk-pktgen,
    # it is required to provide the director where it is installed).
    pktgen_directory = /home/user/software/dpdk_pktgen/dpdk/examples/pktgen/

    # This is the directory where DPDK is installed
    dpdk_directory = /home/user/apexlake/experimental_framework/libraries/Pktgen-DPDK/dpdk/

    # Name of the dpdk-pktgen program that starts the packet generator
    program_name = app/app/x86_64-native-linuxapp-gcc/pktgen

    # DPDK coremask (see DPDK-Pktgen readme)
    coremask = 1f

    # DPDK memory channels (see DPDK-Pktgen readme)
    memory_channels = 3

    # Name of the interface of the pktgen to be used to send traffic (vlan_sender)
    name_if_1 = p1p1

    # Name of the interface of the pktgen to be used to receive traffic (vlan_receiver)
    name_if_2 = p1p2

    # PCI bus address correspondent to if_1
    bus_slot_nic_1 = 01:00.0

    # PCI bus address correspondent to if_2
    bus_slot_nic_2 = 01:00.1


To find the parameters related to names of the NICs and the addresses of the PCI buses
the user may find it useful to run the :term:`DPDK` tool nic_bind as follows:

::

    DPDK_DIR/tools/dpdk_nic_bind.py --status

Lists the NICs available on the system, and shows the available drivers and bus addresses for each interface.
Please make sure to select NICs which are :term:`DPDK` compatible.

Installation and Configuration of smcroute
++++++++++++++++++++++++++++++++++++++++++

The user is required to install smcroute which is used by the framework to
support multicast communications.

The following is the list of commands required to download and install smroute.

::

    cd ~
    git clone https://github.com/troglobit/smcroute.git
    cd smcroute
    git reset --hard c3f5c56
    sed -i 's/aclocal-1.11/aclocal/g' ./autogen.sh
    sed -i 's/automake-1.11/automake/g' ./autogen.sh
    ./autogen.sh
    ./configure
    make
    sudo make install
    cd ..

It is required to do the reset to the specified commit ID.
It is also requires the creation a configuration file using the following
command:

    SMCROUTE_NIC=(name of the nic)

where name of the nic is the name used previously for the variable "name_if_2".
For example:

::

    SMCROUTE_NIC=p1p2

Then create the smcroute configuration file /etc/smcroute.conf

::

    echo mgroup from $SMCROUTE_NIC group 224.192.16.1 > /etc/smcroute.conf


At the end of this procedure it will be necessary to perform the following
actions to add the user to the sudoers:

::

    adduser USERNAME sudo
    echo "user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers


Experiment using SR-IOV Configuration on the Compute Node
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To enable :term:`SR-IOV` interfaces on the physical NIC of the compute node, a
compatible NIC is required.
NIC configuration depends on model and vendor. After proper configuration to
support :term:`SR-IOV`, a proper configuration of OpenStack is required.
For further information, please refer to the SRIOV_ configuration guide

Finalize installation the framework on the system
=================================================

The installation of the framework on the system requires the setup of the project.
After entering into the apexlake directory, it is sufficient to run the following
command.

::

    python setup.py install

Since some elements are copied into the /tmp directory (see configuration file)
it could be necessary to repeat this step after a reboot of the host.
