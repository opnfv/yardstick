#!/bin/bash
##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# installs required packages
# must be run from inside the image (either chrooted or running)

set -ex

if [ $# -eq 1 ]; then
    nameserver_ip=$1

    # /etc/resolv.conf is a symbolic link to /run, restore at end
    rm /etc/resolv.conf
    echo "nameserver $nameserver_ip" > /etc/resolv.conf
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf
fi

# iperf3 only available for trusty in backports
if grep -q trusty /etc/apt/sources.list ; then
    if [ "${YARD_IMG_ARCH}" = "arm64" ]; then
        echo "deb [arch=${YARD_IMG_ARCH}] http://ports.ubuntu.com/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list
    else
        echo "deb http://archive.ubuntu.com/ubuntu/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list
    fi
fi
# Workaround for building on CentOS (apt-get is not working with http sources)
# sed -i 's/http/ftp/' /etc/apt/sources.list

# Force apt to use ipv4 due to build problems on LF POD.
echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

# Add hostname to /etc/hosts.
# Allow console access via pwd
cat <<EOF >/etc/cloud/cloud.cfg.d/10_etc_hosts.cfg
manage_etc_hosts: True
password: RANDOM
chpasswd: { expire: False }
ssh_pwauth: True
EOF
apt-get update
apt-get install -y \
    bc \
    bonnie++ \
    fio \
    git \
    gcc \
    iperf3 \
    ethtool \
    iproute2 \
    linux-tools-common \
    linux-tools-generic \
    lmbench \
    make \
    netperf \
    patch \
    perl \
    rt-tests \
    stress \
    sysstat

CLONE_DEST=/opt/tempT

# remove before cloning
rm -rf -- "${CLONE_DEST}"

git clone https://github.com/kdlucas/byte-unixbench.git "${CLONE_DEST}"

make --directory "${CLONE_DEST}/UnixBench/"

git clone https://github.com/beefyamoeba5/ramspeed.git "${CLONE_DEST}/RAMspeed"

cd "${CLONE_DEST}/RAMspeed/ramspeed-2.6.0"
mkdir temp
bash build.sh

git clone https://github.com/beefyamoeba5/cachestat.git "${CLONE_DEST}/Cachestat"

# restore symlink
ln -sf /run/resolvconf/resolv.conf /etc/resolv.conf
