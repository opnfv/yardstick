##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

#!/bin/bash

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
grep trusty /etc/apt/sources.list && \
    echo "deb http://archive.ubuntu.com/ubuntu/ trusty-backports main restricted universe multiverse" >> /etc/apt/sources.list

# Workaround for building on CentOS (apt-get is not working with http sources)
# sed -i 's/http/ftp/' /etc/apt/sources.list

# Force apt to use ipv4 due to build problems on LF POD.
echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4
# create file to check progress of patching

# ADDING NEWSTUFF
touch /home/patching.txt

echo 'GRUB_CMDLINE_LINUX="resume=/dev/sda1 default_hugepagesz=1G hugepagesz=1G hugepages=1 iommu=on iommu=pt intel_iommu=on"' >> /etc/default/grub

echo 'vm.nr_hugepages=256' >> /etc/sysctl.conf
echo 'huge /mnt/huge hugetlbfs defaults 0 0' >> vi /etc/fstab

echo 'sysctl.conf and fstab modified' >> /home/patching.txt

mkdir /mnt/huge
chmod 777 /mnt/huge

echo 'mnt/huge created and permissions added' >> /home/patching.txt

#touch /etc/dhcp/dhclient-enter-hooks.d/unset_default_router
#chmod 777 /etc/dhcp/dhclient-enter-hooks.d/unset_default_router
#echo '#!/bin/bash' >> /etc/dhcp/dhclient-enter-hooks.d/unset_default_router
#echo 'if [ "$interface" != eth1 ]; then' >> /etc/dhcp/dhclient-enter-hooks.d/unset_default_router
#echo 'echo "Discarding $interface routers: $new_routers"' >> /etc/dhcp/dhclient-enter-hooks.d/unset_default_router
#echo 'unset new_routers' >> /etc/dhcp/dhclient-enter-hooks.d/unset_default_router
#echo 'fi' >> /etc/dhcp/dhclient-enter-hooks.d/unset_default_router

touch /etc/network/interfaces.d/eth1.cfg
chmod 777 /etc/network/interfaces.d/eth1.cfg
echo 'auto eth1' >> /etc/network/interfaces.d/eth1.cfg
echo 'iface eth1 inet dhcp' >> /etc/network/interfaces.d/eth1.cfg

# this needs for checking dpdk status, adding interfaces to dpdk, bind, unbind etc..
# chmod 777 /sys/bus/pci/drivers/virtio-pci/*

# ADDING NEW STUFF ENDED FOR NOW

# Add hostname to /etc/hosts.
cat <<EOF >/etc/cloud/cloud.cfg.d/10_etc_hosts.cfg
manage_etc_hosts: True
EOF

#sleep 20m

apt-get update
apt-get install -y \
    fio \
    gcc \
    git \
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
    sysstat \
    lua5.2

# Continuing adding NEWSTUFF
# pktgen cannot be built with these packages, temporary we specify ones that work
#git clone http://dpdk.org/git/dpdk
#git clone http://dpdk.org/git/apps/pktgen-dpdk

wget "http://dpdk.org/browse/dpdk/snapshot/dpdk-16.04.tar.gz"
tar -xzvf "dpdk-16.04.tar.gz"
mv dpdk-16.04 dpdk
#rm -rf dpdk

wget "http://dpdk.org/browse/apps/pktgen-dpdk/snapshot/pktgen-3.0.00.tar.gz"
tar -zxvf "pktgen-3.0.00.tar.gz"
mv pktgen-3.0.00 pktgen-dpdk
#rm -rf pktgen-dpdk


# get linux headers generic
linux_headers=`apt-cache search linux-headers | grep generic | sed -n 1p | cut -f 1 -d " "`

apt-get install -y \
    libpcap-dev \
    $linux_headers

echo 'dpdk and pktgen-dpdk cloned' >> /home/patching.txt

#sleep 20m

git clone https://github.com/kdlucas/byte-unixbench.git /opt/tempT
make --directory /opt/tempT/UnixBench/
# restore symlink
ln -sf /run/resolvconf/resolv.conf /etc/resolv.conf


