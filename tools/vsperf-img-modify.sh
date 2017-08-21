#!/bin/bash
##############################################################################
# Copyright (c) 2017 Nokia
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

# Force apt to use ipv4 due to build problems on LF POD.
echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

echo 'GRUB_CMDLINE_LINUX="resume=/dev/sda1 default_hugepagesz=1G hugepagesz=1G hugepages=32 iommu=on iommu=pt intel_iommu=on"' >> /etc/default/grub

# Add hostname to /etc/hosts.
# Allow console access via pwd
cat <<EOF >/etc/cloud/cloud.cfg.d/10_etc_hosts.cfg
manage_etc_hosts: True
password: ubuntu
chpasswd: { expire: False }
ssh_pwauth: True
EOF

linuxheadersversion=`echo ls boot/vmlinuz* | cut -d- -f2-`

apt-get update
apt-get install -y \
    linux-headers-$linuxheadersversion \
    screen \
    locate \
    sshpass \
    git

cd /root
git clone -b stable/danube https://gerrit.opnfv.org/gerrit/vswitchperf

# do not compile ovs and qemu
sed -i.bak -e 's/^\(SUBBUILDS\ =\ src_vanilla\)/#\1/' \
           -e 's/^\(SUBDIRS\ += ovs.*\)/#\1/' \
           -e 's/^\(SUBDIRS\ += qemu.*\)/#\1/' \
    vswitchperf/src/Makefile
# If these paths do not exist, vsperf wont start
mkdir -p /root/vswitchperf/src/ovs/ovs/ovsdb/
touch /root/vswitchperf/src/ovs/ovs/ovsdb/ovsdb-tool
touch /root/vswitchperf/src/ovs/ovs/ovsdb/ovsdb-server
mkdir -p /root/vswitchperf/src/qemu/qemu/x86_64-softmmu/
touch /root/vswitchperf/src/qemu/qemu/x86_64-softmmu/qemu-system-x86_64
mkdir -p /root/vswitchperf/src/ovs/ovs/utilities/
touch /root/vswitchperf/src/ovs/ovs/utilities/ovs-dpctl
touch /root/vswitchperf/src/ovs/ovs/utilities/ovs-vsctl
touch /root/vswitchperf/src/ovs/ovs/utilities/ovs-ofctl
touch /root/vswitchperf/src/ovs/ovs/utilities/ovs-appctl
mkdir -p /root/vswitchperf/src/ovs/ovs/vswitchd/
touch /root/vswitchperf/src/ovs/ovs/vswitchd/vswitch.ovsschema
touch /root/vswitchperf/src/ovs/ovs/vswitchd/ovs-vswitchd

# restore symlink
#ln -sf /run/resolvconf/resolv.conf /etc/resolv.conf
