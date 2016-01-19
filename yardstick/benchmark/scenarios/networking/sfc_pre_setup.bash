#!/bin/bash
set -e

sudo ifconfig br-int up
sudo ip route add 11.0.0.0/24 dev br-int


# download and create image
source /opt/admin-openrc.sh 
wget https://www.dropbox.com/s/focu44sh52li7fz/sfc_cloud.qcow2
openstack image create sfc --public --file ./sfc_cloud.qcow2

#create flavor
openstack flavor create sfc_custom --ram 1000 --disk 5 --public


