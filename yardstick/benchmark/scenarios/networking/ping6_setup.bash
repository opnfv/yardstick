#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


# download and create image
openrc=$1
external_network=$2
echo "openrc=$openrc"
echo "external_network=$external_network"
echo "nameserver 8.8.4.4" >> /etc/resolv.conf
source $openrc

fedora_img="Fedora-Cloud-Base-22-20150521.x86_64.qcow2"
if [ ! -f "$fedora_img" ]; then
    wget https://download.fedoraproject.org/pub/fedora/linux/releases/22/Cloud/x86_64/Images/${fedora_img} >/dev/null 2>&1
fi

glance image-create --name 'Fedora22' --disk-format qcow2 \
--container-format bare --file ./Fedora-Cloud-Base-22-20150521.x86_64.qcow2


# create router
neutron router-create ipv4-router
neutron router-create ipv6-router


# create (ipv4,ipv6)router and net and subnet
neutron net-create ipv4-int-network1
neutron net-create ipv6-int-network2

# Create IPv4 subnet and associate it to ipv4-router
neutron subnet-create --name ipv4-int-subnet1 \
--dns-nameserver 8.8.8.8 ipv4-int-network1 20.0.0.0/24
neutron router-interface-add ipv4-router ipv4-int-subnet1

#  Associate the net04_ext to the Neutron routers
neutron router-gateway-set ipv6-router $external_network
neutron router-gateway-set ipv4-router $external_network

# Create two subnets, one IPv4 subnet ipv4-int-subnet2 and
# one IPv6 subnet ipv6-int-subnet2 in ipv6-int-network2, and associate both subnets to ipv6-router
neutron subnet-create --name ipv4-int-subnet2 --dns-nameserver 8.8.8.8 ipv6-int-network2 10.0.0.0/24
neutron subnet-create --name ipv6-int-subnet2 \
 --ip-version 6 --ipv6-ra-mode slaac --ipv6-address-mode slaac ipv6-int-network2 2001:db8:0:1::/64


neutron router-interface-add ipv6-router ipv4-int-subnet2
neutron router-interface-add ipv6-router ipv6-int-subnet2


# create key
nova keypair-add vRouterKey > ~/vRouterKey

# Create ports for vRouter
neutron port-create --name eth0-vRouter --mac-address fa:16:3e:11:11:11 ipv6-int-network2
neutron port-create --name eth1-vRouter --mac-address fa:16:3e:22:22:22 ipv4-int-network1

# Create ports for VM1 and VM2.
neutron port-create --name eth0-VM1 --mac-address fa:16:3e:33:33:33 ipv4-int-network1
neutron port-create --name eth0-VM2 --mac-address fa:16:3e:44:44:44 ipv4-int-network1

# Update ipv6-router with routing information to subnet 2001:db8:0:2::/64
neutron router-update ipv6-router \
 --routes type=dict list=true destination=2001:db8:0:2::/64,nexthop=2001:db8:0:1:f816:3eff:fe11:1111

# vRouter boot
nova boot --image Fedora22 --flavor m1.small \
--user-data ./metadata.txt \
--nic port-id=$(neutron port-list | grep -w eth0-vRouter | awk '{print $2}') \
--nic port-id=$(neutron port-list | grep -w eth1-vRouter | awk '{print $2}') \
--key-name vRouterKey vRouter

# VM create
nova boot --image Fedora22  --flavor m1.small \
--nic port-id=$(neutron port-list | grep -w eth0-VM1 | awk '{print $2}') \
--key-name vRouterKey VM1

nova boot --image Fedora22  --flavor m1.small \
--nic port-id=$(neutron port-list | grep -w eth0-VM2 | awk '{print $2}') \
--key-name vRouterKey VM2

sleep 60

nova list
# disable eth0-VM1, eth0-VM2, eth0-vRouter, eth1-vRouter port-security
for port in eth0-VM1 eth0-VM2 eth0-vRouter eth1-vRouter
do
    neutron port-update --no-security-groups $port
    neutron port-update $port --port-security-enabled=False
    neutron port-show $port | grep port_security_enabled
done
