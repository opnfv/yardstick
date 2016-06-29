#!/bin/bash

# installs dpdk and pktgen packages on modified image

# PREREQUISITES
# modified image (yardstick-wily-server) must be uploaded to OpenStack
# heat must be installed: apt-get install python-heatclient, python-glanceclient, python-nova
# use the yardstick keypaire, you can find key files under yardstick/yardsitck/resource/files.

# TODO
# automatic clean - delete stack (only the image is needed for later use)

stackname="yardstick-modify-stack"
template=dpdk_install.yml
new_image_name="yardstick-image-pktgen-ready"

# TODO: with Mitaka release this command starts with openstack heat stack-create..
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

status=$(nova image-create --poll $stackname $new_image_name)
if [[ "$status" =~ "Finished" ]];then
  echo "$new_image_name finished"
fi

openstack stack delete $stackname
