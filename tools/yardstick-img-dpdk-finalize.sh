#!/bin/bash

# installs dpdk and pktgen packages on modified image

# PREREQUISITES
# modified image (yardstick-wily-server) must be uploaded to OpenStack
# heat must be installed: apt-get install python-heatclient, python-glanceclient, python-nova
# must have a public yardstick-key uploaded in openstack
# must have a proper flavor for the image (i.e. m1.small)

# TODO
# automatic clean - delete stack (only the image is needed for later use)

stackname="yardstick-modify-stack"
template=dpdk_install.yml
new_image_name="yardstick-image-pktgen-ready"

heat stack-create $stackname -f $template

progress="WARMING_UP"

while [ "$progress" != "CREATE_COMPLETE" ]
do
  show_output=$(heat stack-show $stackname)
  progress=$(echo $show_output | sed 's/^.*stack_status . \([^ ]*\).*$/\1/')
done

nova stop $stackname

uuid=$(heat output-show -v $stackname vm_uuid)

if [ $? -ne 0 ]
then
  uuid=$(heat output-show $stackname vm_uuid)
fi

pluuid=`echo "${uuid:1:-1}"`
echo $pluuid
nova image-create --poll $pluuid $new_image_name
