Welcome to ApexLake's documentation!
====================================
ApexLake is a framework that provides automatic execution of experiment and related data collection to help
the user validating the infrastructure from a Virtual Network Function perspective.

Install framework and dependencies
----------------------------------
Before to start the framework, a set of dependencies are required.
In the following a set of instructions to be executed on the Linux shell to install dependencies and configure the environment.

1. Install dependencies
    - # apt-get install python-dev
    - # apt-get install python-pip
    - # apt-get install python-mock
    - # apt-get install tcpreplay
    - # apt-get install libpcap-dev

2. Install the framework on the system
    - # python setup.py install

3. Source OpenStack openrc file
    - $ source openrc

4. Create 2 Networks (and subnets) based on VLANs (provider:network_type = vlan) in Neutron
    - $ neutron net-create apexlake_inbound_network --provider:network_type vlan --provider:physical_network physnet1
    - $ neutron subnet-create apexlake_inbound_network 192.168.0.0/24 --name apexlake_inbound_subnet
    - $ neutron net-create apexlake_outbound_network --provider:network_type vlan --provider:physical_network physnet1
    - $ neutron subnet-create apexlake_outbound_network 192.168.1.0/24 --name apexlake_outbound_subnet

5. Insert VLAN tags related to the networks have to ApexLake, either:
    - into the "conf.cfg" configuration file, or
    - through the Python API.


Install and configure DPDK Pktgen
+++++++++++++++++++++++++++++++++
The execution of the framework is based on DPDK Pktgen.
If DPDK Pktgen has not been installed on the system by the user, it is necessary to download, compile and configure it.
The user can create a directory and download the dpdk packet generator source code:
    - $ cd experimental_framework/libraries
    - $ mkdir dpdk_pktgen
    - $ git clone https://github.com/pktgen/Pktgen-DPDK.git

For the installation and configuration of DPDK and DPDK Pktgen please follow the official DPDK Pktgen README file.
Once the installation is completed, it is necessary to load the DPDK kernel driver, as follow:
    - # insmod uio
    - # insmod DPDK_DIR/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko

It is required to properly set the configuration file according to the system on Pktgen runs on.
An example is provided in the following:

    - [PacketGen]
    - packet_generator = dpdk_pktgen
    - pktgen_directory = /home/user/apexlake/experimental_framework/libraries/dpdk_pktgen/dpdk/examples/pktgen/
        -- This is the directory where the packet generator is installed (if the user previously installed dpdk-pktgen, it is required to provide the director where it is installed).
    - dpdk_directory = /home/user/apexlake/experimental_framework/libraries/Pktgen-DPDK/dpdk/
        -- This is the directory where DPDK is installed
    - program_name = app/app/x86_64-native-linuxapp-gcc/pktgen
        -- This is the name of the dpdk-pktgen program that starts the packet generator
    - coremask = 1f
        -- DPDK coremask (see DPDK-Pktgen readme)
    - memory_channels = 3
        -- DPDK memory channels (see DPDK-Pktgen readme)
    - name_if_1 = p1p1
        -- Name of the interface of the pktgen to be used to send traffic
    - name_if_2 = p1p2
        -- Name of the interface of the pktgen to be used to receive traffic
    - bus_slot_nic_1 = 01:00.0
        -- PCI bus address correspondent to the if_1
    - bus_slot_nic_2 = 01:00.1
        -- PCI bus address correspondent to the if_2


To find the parameters related to names of the NICs and addresses of the PCI buses the user may find useful to run the DPDK tool nic_bind as follows:

    - $ DPDK_DIR/tools/dpdk_nic_bind.py --status

which lists the NICs available on the system, show the available drivers and bus addresses for each interface.
Please make sure to select NICs which are DPDK compatible.

Installation and configuration of smcroute
++++++++++++++++++++++++++++++++++++++++++
The user is required to install smcroute which is used by the framework to support multicast communications.
In the following a list of commands to be ran to download and install smroute is provided.

    - $ cd ~
    - $ git clone https://github.com/troglobit/smcroute.git
    - $ cd smcroute
    - $ sed -i 's/aclocal-1.11/aclocal/g' ./autogen.sh
    - $ sed -i 's/automake-1.11/automake/g' ./autogen.sh
    - $ ./autogen.sh
    - $ ./configure
    - $ make
    - $ sudo make install
    - $ cd ..

It is also required to create a configuration file using the following command:

    - $ SMCROUTE_NIC=(name of the nic)

where name of the nic is the name used previously for the variable "name_if_2".
In the example it would be:

    - $ SMCROUTE_NIC=p1p2

Then create the smcroute configuration file /etc/smcroute.conf

    - $echo mgroup from $SMCROUTE_NIC group 224.192.16.1 > /etc/smcroute.conf


Experiment using SR-IOV configuration on the compute node
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
In order to enable SR-IOV interfaces on the physical NIC of the compute node, a compatible NIC is required.
NIC configuration depends on model and vendor. After proper configuration to support SR-IOV, a proper configuration of openstack is required.
For further information, please look at the following link:
https://wiki.openstack.org/wiki/SR-IOV-Passthrough-For-Networking
