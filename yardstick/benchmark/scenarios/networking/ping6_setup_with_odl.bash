#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
# need to debug

# download and create image
openrc=$1
external_network=$2
echo "openrc=$openrc"
echo "external_network=$external_network"
source $openrc
wget https://download.fedoraproject.org/pub/fedora/linux/releases/22/Cloud/x86_64/Images/Fedora-Cloud-Base-22-20150521.x86_64.qcow2
glance image-create --name 'Fedora22' --disk-format qcow2 \
--container-format bare --file ./Fedora-Cloud-Base-22-20150521.x86_64.qcow2

# create router
neutron router-create ipv4-router
neutron router-create ipv6-router

#  Associate the net04_ext to the Neutron routers
neutron router-gateway-set ipv6-router $external_network
neutron router-gateway-set ipv4-router $external_network

# create two ipv4 networks with associated subnets
neutron net-create ipv4-int-network1
neutron net-create ipv4-int-network2

# Create IPv4 subnet and associate it to ipv4-router
neutron subnet-create --name ipv4-int-subnet1 \
--dns-nameserver 8.8.8.8 ipv4-int-network1 20.0.0.0/24

# Associate the ipv4-int-subnet1 with ipv4-router
neutron router-interface-add ipv4-router ipv4-int-subnet1

# BIN-HU: Here, for scenario 2, ipv6-int-subnet2 cannot be created automatically because of a bug in ODL
# BIN-HU: we need to manually spawn a RADVD daemon in ipv6-router namespace

# Create an IPv4 subnet ipv4-int-subnet2 and associate it with ipv6-router
neutron subnet-create --name ipv4-int-subnet2 --dns-nameserver 8.8.8.8 ipv4-int-network2 10.0.0.0/24

neutron router-interface-add ipv6-router ipv4-int-subnet2

# BIN-HU: for the reason above in scenario 2, we need to remove the following command

# create key
nova keypair-add vRouterKey > ~/vRouterKey

# Create ports for vRouter
neutron port-create --name eth0-vRouter --mac-address fa:16:3e:11:11:11 ipv4-int-network2
neutron port-create --name eth1-vRouter --mac-address fa:16:3e:22:22:22 ipv4-int-network1

# Create ports for VM1 and VM2.
neutron port-create --name eth0-VM1 --mac-address fa:16:3e:33:33:33 ipv4-int-network1
neutron port-create --name eth0-VM2 --mac-address fa:16:3e:44:44:44 ipv4-int-network1


# Hope you are cloning the following repo for some files like radvd.conf and metadata.txt
# JFYI, metadata.txt is available at the following git repo. https://github.com/sridhargaddam/opnfv_os_ipv6_poc/blob/master/metadata.txt
# vRouter boot
nova boot --image Fedora22 --flavor m1.small \
--user-data ./metadata.txt \
--nic port-id=$(neutron port-list | grep -w eth0-vRouter | awk '{print $2}') \
--nic port-id=$(neutron port-list | grep -w eth1-vRouter | awk '{print $2}') \
--key-name vRouterKey vRouter

# BIN-HU: Note that some other parameters might be needed in Scenario 2, if it does not work
# BIN-HU: Refer to http://artifacts.opnfv.org/ipv6/docs/setupservicevm/4-ipv6-configguide-servicevm.html#boot-two-other-vms-in-ipv4-int-network1
# BIN-HU: Section 3.5.7
# VM create
nova boot --image Fedora22  --flavor m1.small \
--nic port-id=$(neutron port-list | grep -w eth0-VM1 | awk '{print $2}') \
--key-name vRouterKey VM1

nova boot --image Fedora22  --flavor m1.small \
--nic port-id=$(neutron port-list | grep -w eth0-VM2 | awk '{print $2}') \
--key-name vRouterKey VM2

nova list

# BIN-HU: Now we need to spawn a RADVD daemon inside ipv6-router namespace
# BIN-HU: The following is specific for Scenario 2 to spawn a RADVD daemon in ipv6-router namespace
# BIN-HU: Refer to http://artifacts.opnfv.org/ipv6/docs/setupservicevm/4-ipv6-configguide-servicevm.html#spawn-radvd-in-ipv6-router
# BIN-HU: Section 3.5.8, Steps SETUP-SVM-24 through SETUP-SVM-30
# BIN-HU: Also note that in case of HA deployment, ipv6-router created in previous step
# BIN-HU: could be in any of the controller node. Thus you need to identify in which controller node
# BIN-HU: ipv6-router is created in order to manually spawn RADVD daemon inside the ipv6-router
# BIN-HU: namespace in the following steps.
# BIN-HU: Just FYI: the following command in Neutron will display the controller on which the
# BIN-HU: ipv6-router is spawned.
neutron l3-agent-list-hosting-router ipv6-router

# find host which is located by ipv6-router, but need to debug
host_num=$(neutron l3-agent-list-hosting-router ipv6-router | grep True | awk -F [=\ ] '{printf $4}')
ssh $host_num

# BIN-HU: identify the ipv6-router namespace and move to the namespace
sudo ip netns exec qrouter-$(neutron router-list | grep -w ipv6-router | awk '{print $2}') bash

# BIN-HU: Inside ipv6-router namespace, configure the IPv6 address on the <qr-xxx> interface.
export router_interface=$(ip a s | grep -w "global qr-*" | awk '{print $7}')
ip -6 addr add 2001:db8:0:1::1 dev $router_interface

# BIN-HU: Update the sample file radvd.conf with $router_interface
sed -i 's/$router_interface/'$router_interface'/g' ~/br-ex.radvd.conf

# BIN-HU: Spawn a RADVD daemon to simulate an external router
radvd -C ~/br-ex.radvd.conf -p ~/br-ex.pid.radvd

# BIN-HU: Add an IPv6 downstream route pointing to the eth0 interface of vRouter.
ip -6 route add 2001:db8:0:2::/64 via 2001:db8:0:1:f816:3eff:fe11:1111

# BIN-HU: you can double check the routing table
ip -6 route show

exit
# BIN-HU: End of Scenario 2, and you can continue to SSH etc., the same as Scenario 1
