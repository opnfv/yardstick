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
if [ $YARD_IMG_ARCH = "arm64" ]; then
grep -q trusty /etc/apt/sources.list && \
    echo "deb [arch=arm64] http://ports.ubuntu.com/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list
else
grep -q trusty /etc/apt/sources.list && \
    echo "deb http://archive.ubuntu.com/ubuntu/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list
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
if [ $YARD_IMG_ARCH = "arm64" ]; then
apt-get install -y \
    linux-headers-$(echo $VIVID_KERNEL_VERSION | cut -d'-' -f3,4,5) \
    unzip
#resize root parition (/dev/vdb1) It is supposed to be default but the image is booted differently for arm64
cat <<EOF >/etc/cloud/cloud.cfg.d/15_growpart.cfg
#cloud-config
bootcmd:
 - [growpart, /dev/vdb, 1]
EOF
fi
apt-get install -y \
    fio \
    git \
    gcc \
    iperf3 \
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

if [ $YARD_IMG_ARCH = "arm64" ]; then
    wget https://github.com/kdlucas/byte-unixbench/archive/master.zip
    unzip master.zip && rm master.zip
    mkdir /opt/tempT
    mv byte-unixbench-master/UnixBench /opt/tempT
    git apply --directory=/opt/tempT/ unixbench_aarch64_build.patch
else
    git clone https://github.com/kdlucas/byte-unixbench.git /opt/tempT
fi
make --directory /opt/tempT/UnixBench/

if [ $YARD_IMG_ARCH = "arm64" ]; then
    wget https://github.com/beefyamoeba5/ramspeed/archive/master.zip
    unzip master.zip && rm master.zip
    mkdir /opt/tempT/RAMspeed
    mv ramspeed-master/* /opt/tempT/RAMspeed/
else
    git clone https://github.com/beefyamoeba5/ramspeed.git /opt/tempT/RAMspeed
fi
cd /opt/tempT/RAMspeed/ramspeed-2.6.0
mkdir temp
bash build.sh

if [ $YARD_IMG_ARCH = "arm64" ]; then
    wget https://github.com/beefyamoeba5/cachestat/archive/master.zip
    unzip master.zip && rm master.zip
else
    git clone https://github.com/beefyamoeba5/cachestat.git /opt/tempT/Cachesta
fi
mv cachestat-master/cachestat /opt/tempT

# restore symlink
ln -sf /run/resolvconf/resolv.conf /etc/resolv.conf
