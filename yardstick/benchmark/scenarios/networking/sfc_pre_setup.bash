#!/bin/bash
set -e

# download and create image
wget https://www.dropbox.com/s/focu44sh52li7fz/sfc_cloud.qcow2
glance image-create --name sfc --disk-format qcow2 --container-format bare --file sfc_cloud.qcow2

#create flavor
nova flavor-create --is-public true sfc_custom 666 1000 5 2
