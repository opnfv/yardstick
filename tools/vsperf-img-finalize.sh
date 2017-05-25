#!/bin/bash
##############################################################################
# Copyright (c) 2017 Nokia
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# PREREQUISITES
# modified image (yardstick-vsperf) must be uploaded to OpenStack
# must have a proper flavor (vsperf-flavor) for the image e.g.
# nova flavor-create vsperf-flavor auto 8192 80 6
# nova flavor-key vsperf-flavor set hw:numa_nodes=1
# nova flavor-key vsperf-flavor set hw:mem_page_size=1GB
# nova flavor-key vsperf-flavor set hw:cpu_policy=dedicated
# nova flavor-key vsperf-flavor set hw:vif_multiqueue_enabled=true

stackname="vsperf-install-stack"
template=vsperf_install.yml
new_image_name="yardstick-vsperf-server"

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

# has to stop the instance before taking the snapshot
nova stop $stackname
sleep 10

status=$(nova image-create --poll $stackname $new_image_name)
if [[ "$status" =~ "Finished" ]];then
  echo "$new_image_name finished"
fi

nova delete $stackname
sleep 10
openstack stack delete --yes $stackname
