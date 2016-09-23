#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
openrc=$1
echo "openrc=$openrc"
source $openrc
external_network=$2
echo "external_network=$external_network"
# delete VM
nova delete VM1
nova delete VM2
nova delete vRouter
#clear routes
neutron router-update ipv6-router --routes action=clear

#VM1,VM2 port delete
neutron port-delete --name eth0-VM1
neutron port-delete --name eth0-VM2

#vRouter port delete
neutron port-delete --name eth0-vRouter
neutron port-delete --name eth1-vRouter

#delete key
nova keypair-delete vRouterKey

#delete ipv6 router interface
neutron router-interface-delete ipv6-router ipv6-int-subnet2
neutron router-interface-delete ipv6-router ipv4-int-subnet2

#delete subnet
neutron subnet-delete --name ipv6-int-subnet2
neutron subnet-delete --name ipv4-int-subnet2

#clear gateway
neutron router-gateway-clear ipv4-router $external_network
neutron router-gateway-clear ipv6-router $external_network

#delete ipv4 router interface
neutron router-interface-delete ipv4-router ipv4-int-subnet1
neutron subnet-delete --name ipv4-int-subnet1

#delete network
neutron net-delete ipv6-int-network2
neutron net-delete ipv4-int-network1

# delete router
neutron router-delete ipv4-router
neutron router-delete ipv6-router

# delete glance image
glance --os-image-api-version 1 image-delete Fedora22
