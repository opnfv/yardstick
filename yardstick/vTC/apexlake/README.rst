.. _DPDK: http://dpdk.org/doc/nics
.. _DPDK-pktgen: https://github.com/Pktgen/Pktgen-DPDK/
.. _SRIOV: https://wiki.openstack.org/wiki/SR-IOV-Passthrough-For-Networking
.. _PORTSEC: https://wiki.openstack.org/wiki/Neutron/ML2PortSecurityExtensionDriver

===========================
Apexlake installation guide
===========================
ApexLake is a framework that provides automatic execution of experiments and related data collection to help
the user validating the infrastructure from the perspective of a Virtual Network Function.
To do so in the context of Yardstick, the virtual Traffic Classifier network function is utilized.


Hardware dependencies to run the framework
==========================================
In order to run the framework some hardware dependencies are required to run ApexLake.

The framework needs to be installed on a physical node where the DPDK packet DPDK-pktgen_
can be correctly installed and executed.
That requires for the packet generator to have 2 NICs DPDK_ Compatible.

The 2 NICs will be connected to the switch where the Openstack VM network is managed.

The switch is required to support multicast traffic and snooping protocol.

The corresponding ports to which the cables are connected will be configured as VLAN trunks
using two of the VLAN IDs available for Neutron.
The mentioned VLAN IDs will be required in further configuration steps.


Software dependencies to run the framework
==========================================
Before to start the framework, a set of dependencies are required to be installed.
In the following a set of instructions to be executed on the Linux shell to install dependencies
and configure the environment is presented.

1. Install dependencies.

To install the dependencies required by the framework it is necessary install the following packages.
The following example is provided for Ubuntu and need to be executed as root.
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

In order to support traffic generation and management by the virtual Traffic Classifier, 
the configuration of the port security driver extension is required for Neutron.
For further details please follow the following link: PORTSEC_
This step can be skipped in case the target OpenStack is Juno or Kilo release, 
but it is required to support Liberty.
It is therefore required to indicate the release version in the configuration file apexlake.conf.

4. Create 2 Networks based on VLANs in Neutron.

In order for the network communication between the packet generator and the Compute node to
work fine, it is required to create through Neutron two networks and map those on the VLAN IDs
that have been previously used for the configuration on the physical switch.
The underlying switch needs to be configured accordingly.
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
The image can be downloaded on the local machine and loaded on Glance using the following commands:
::

    wget cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img
    glance image-create \
            --name ubuntu1404 \
            --is-public true \
            --disk-format qcow \
            --container-format bare \
            --file trusty-server-cloudimg-amd64-disk1.img

6. Configure the Test Cases.

The VLAN tags are also required into the test case Yardstick yaml file as parameters the following test cases:
    - TC 006
    - TC 007
    - TC 020
    - TC 021


Install and configure DPDK Pktgen
+++++++++++++++++++++++++++++++++
The execution of the framework is based on DPDK Pktgen.
If DPDK Pktgen has not been installed on the system by the user, it is necessary to download, compile and configure it.
The user can create a directory and download the dpdk packet generator source code:
::

    cd experimental_framework/libraries
    mkdir dpdk_pktgen
    git clone https://github.com/pktgen/Pktgen-DPDK.git

For the installation and configuration of DPDK and DPDK Pktgen please follow the official DPDK Pktgen README file.
Once the installation is completed, it is necessary to load the DPDK kernel driver, as follow:
::

    insmod uio
    insmod DPDK_DIR/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko

It is required to properly set the configuration file according to the system on Pktgen runs on.
A description of the required configuration parameters and examples is provided in the following:
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


To find the parameters related to names of the NICs and addresses of the PCI buses
the user may find useful to run the DPDK tool nic_bind as follows:
::

    DPDK_DIR/tools/dpdk_nic_bind.py --status

which lists the NICs available on the system, show the available drivers and bus addresses for each interface.
Please make sure to select NICs which are DPDK compatible.

Installation and configuration of smcroute
++++++++++++++++++++++++++++++++++++++++++
The user is required to install smcroute which is used by the framework to support multicast communications.
In the following a list of commands to be ran to download and install smroute is provided.
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
It is also required to create a configuration file using the following command:

    SMCROUTE_NIC=(name of the nic)

where name of the nic is the name used previously for the variable "name_if_2".
In the example it would be:
::

    SMCROUTE_NIC=p1p2

Then create the smcroute configuration file /etc/smcroute.conf
::

    echo mgroup from $SMCROUTE_NIC group 224.192.16.1 > /etc/smcroute.conf


At the end of this procedure it will be necessary to perform the following actions to add the user to the sudoers:
::

    adduser USERNAME sudo
    echo "user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers


Experiment using SR-IOV configuration on the compute node
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
In order to enable SR-IOV interfaces on the physical NIC of the compute node, a compatible NIC is required.
NIC configuration depends on model and vendor. After proper configuration to support SR-IOV,
a proper configuration of openstack is required.
For further information, please look at the _SRIOV configuration guide


Finalize installation the framework on the system
=================================================

The installation of the framework on the system requires the setup of the project.
After entering into the apexlake directory, it is sufficient to run the following command.
::

    python setup.py install

Since some elements are copied into the /tmp directory (see configuration file) it could be necessary
to repeat this step after a reboot of the host.
