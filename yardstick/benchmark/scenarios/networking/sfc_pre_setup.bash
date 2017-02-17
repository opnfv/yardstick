#!/bin/bash
##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

# download and create image
#wget https://www.dropbox.com/s/focu44sh52li7fz/sfc_cloud.qcow2
glance image-create --name sfc --disk-format qcow2 --container-format bare --file SF.qcow2


#create flavor
openstack flavor create custom --ram 1500 --disk 10 --public
