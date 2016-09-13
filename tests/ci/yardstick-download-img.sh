#!/bin/bash
# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2016 ZTE and others.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
set -o errexit
set -o pipefail


cirros_img='cirros-0.3.3-x86_64-disk.img'
cirros_url='http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img'

IMGSTORE="/home/opnfv/images"

download_cirros_img() {
    # using IMGs from local storage directory
    # check if we already have the IMG to avoid redownload
    if [[ -f "$IMGSTORE/$cirros_img" ]]; then
        echo "$cirros_img exists locally. Skipping the download and using the local file"
        echo
    else
        # download the file
        echo "Downloading the ${cirros_img} using URL ${cirros_url}"
        echo "This could take some time..."
        echo "--------------------------------------------------------"
        echo
        wget -c -O $IMGSTORE/$cirros_img $cirros_url
    fi
}

YARD_IMG_ARCH=amd64
export YARD_IMG_ARCH

host=${HOST:-"cloud-images.ubuntu.com"}
release=${RELEASE:-"trusty"}
image_path="${release}/current/${release}-server-cloudimg-${YARD_IMG_ARCH}-disk1.img"
image_url=${IMAGE_URL:-"https://${host}/${image_path}"}
md5sums_path="${release}/current/MD5SUMS"
md5sums_url=${MD5SUMS_URL:-"https://${host}/${md5sums_path}"}
filename=$(basename $image_url)
# download and checksum base image, conditionally if local copy is outdated
download_ubuntu_img() {
    cd $IMGSTORE
    rm -f MD5SUMS # always download the checksum file to a detect stale image
    wget $md5sums_url
    test -e $filename || wget -nc --progress=dot:giga $image_url
    grep $filename MD5SUMS | md5sum -c ||
    if [ $? -ne 0 ]; then
        rm $filename
        wget -nc --progress=dot:giga $image_url
        grep $filename MD5SUMS | md5sum -c
    fi
}


download_cirros_img

download_ubuntu_img

workspace=${WORKSPACE:-"/tmp/workspace/yardstick"}
test -d $workspace || mkdir -p $workspace
# copy ubuntu image to /tmp/workspace/yardstick, avoid downloading it again in yardstick-image-modify
echo "copy $filename to $workspace"
cp $IMGSTORE/$filename $workspace/$filename

echo "Done!"
