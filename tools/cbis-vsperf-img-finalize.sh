#!/bin/bash

# installs dpdk and pktgen packages on modified image

# PREREQUISITES
# modified image (yardstick-vsperf) must be uploaded to OpenStack

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
