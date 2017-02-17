#!/bin/bash
##############################################################################
# Copyright (c) 2017 ZTE corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


# installs dpdk and pktgen packages on modified image

# PREREQUISITES
# modified image (yardstick-wily-server) must be uploaded to OpenStack
# heat must be installed: apt-get install python-heatclient, python-glanceclient, python-nova
# must have a public yardstick-key uploaded in openstack
# must have a proper flavor for the image (i.e. m1.small)


stackname="yardstick-modify-stack"
template=dpdk_install.yml
new_image_name="yardstick-image-pktgen-ready"

openstack stack create $stackname -f yaml -t $template
progress="WARMING_UP"

while [ "$progress" != "CREATE_COMPLETE" ]
do
  sleep 10
  echo "check stack status......."
  show_output=$(openstack stack show $stackname)
  progress=$(echo $show_output | sed 's/^.*stack_status . \([^ ]*\).*$/\1/')
  echo "$progress"
  if [ "$progress" == "CREATE_FAILED" ];then
    echo "create $stackname failed"
    exit 1
  fi
done

# workaround: Without wait time, the file size of pktgen is zero in the snapshot.
sleep 60

status=$(nova image-create --poll $stackname $new_image_name)
if [[ "$status" =~ "Finished" ]];then
  echo "$new_image_name finished"
fi

nova delete $stackname
sleep 10
openstack stack delete --yes $stackname
