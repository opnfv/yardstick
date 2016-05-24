#!/bin/bash
set -e

# download and create image
#wget https://www.dropbox.com/s/focu44sh52li7fz/sfc_cloud.qcow2
glance image-create --name sfc --disk-format qcow2 --container-format bare --file SF.qcow2


#create flavor
openstack flavor create custom --ram 1500 --disk 10 --public
