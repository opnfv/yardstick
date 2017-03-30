#!/bin/bash
# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

INSTALL_BIN_PATH="/opt/nsb_bin"
DPDK_DOWNLOAD="http://dpdk.org/browse/dpdk/snapshot/dpdk-16.07.zip"

install_dpdk() {
				mkdir -p $INSTALL_BIN_PATH
				if [ -d "$INSTALL_BIN_PATH/dpdk-16.07" ]; then
								echo "DPDK already installed make sure.. igb_uio is loaded."
				else
								echo "Build DPDK 16.07..."
								pushd .
								rm -rf ${DPDK_DOWNLOAD##*/}
								rm -rf "$REPO_DIR/dpdk-16.07/"
								if [ ! -e ${DPDK_DOWNLOAD##*/} ] ; then
												wget ${DPDK_DOWNLOAD}
								fi
								unzip -o ${DPDK_DOWNLOAD##*/}

								cd dpdk-16.07
								make config T=x86_64-native-linuxapp-gcc O=x86_64-native-linuxapp-gcc
								cd x86_64-native-linuxapp-gcc
								echo "Enable Port Stats..."
								sed -i -e 's/CONFIG_RTE_PORT_STATS_COLLECT=n/CONFIG_RTE_PORT_STATS_COLLECT=y/g' .config
								sed -i -e 's/CONFIG_RTE_PORT_PCAP=n/CONFIG_RTE_PORT_PCAP=y/g' .config
								sed -i -e 's/CONFIG_RTE_TABLE_STATS_COLLECT=n/CONFIG_RTE_TABLE_STATS_COLLECT=y/g' .config
								sed -i -e 's/CONFIG_RTE_PIPELINE_STATS_COLLECT=n/CONFIG_RTE_PIPELINE_STATS_COLLECT=y/g' .config
								make

								echo "Load DPDK modules and setup hugepages"
								modprobe uio
								mkdir -p "/lib/modules/$(uname -r)/extra"
								cp -r "kmod/igb_uio.ko" "/lib/modules/$(uname -r)/extra"
								depmod -a
								modprobe igb_uio
								sh -c "echo 'uio\nigb_uio\n' > /etc/modules-load.d/nsb.conf"

								HUGEPGSZ=$(cat < /proc/meminfo  | grep Hugepagesize | cut -d : -f 2 | tr -d ' ')
								Pages=4
								if [[ "$HUGEPGSZ" = "2048kB" ]] ; then
												Pages=4096
								fi
								grep nr_hugepages /etc/sysctl.conf
								if [[ "$?" -eq '1' ]] ; then
												sh -c "echo 'vm.nr_hugepages=$Pages' >> /etc/sysctl.conf"
								fi
								mv "$REPO_DIR/dpdk-16.07" "$INSTALL_BIN_PATH"
								rm dpdk-16.07.zip
				fi
				export RTE_SDK="$INSTALL_BIN_PATH/dpdk-16.07"
				export RTE_TARGET=x86_64-native-linuxapp-gcc

				if [ ! -f "$INSTALL_BIN_PATH/vPE_vnf" ]; then
								pushd .
								echo "Building vPE VNF..."
								cd $INSTALL_BIN_PATH/dpdk-16.07/examples/ip_pipeline/
								make clean
								make
								cp build/ip_pipeline $INSTALL_BIN_PATH/vPE_vnf
								popd
				fi
				echo "Done"
}

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

echo 'GRUB_CMDLINE_LINUX="resume=/dev/sda1 default_hugepagesz=1G hugepagesz=1G hugepages=2 iommu=on iommu=pt intel_iommu=on"' >> /etc/default/grub
echo 'huge /mnt/huge hugetlbfs defaults 0 0' >> vi /etc/fstab

mkdir /mnt/huge
chmod 777 /mnt/huge

for i in {1..2}
do
    touch /etc/network/interfaces.d/eth$i.cfg
    chmod 777 /etc/network/interfaces.d/eth$i.cfg
    echo "auto eth$i" >> /etc/network/interfaces.d/eth$i.cfg
    echo "iface eth$i inet dhcp" >> /etc/network/interfaces.d/eth$i.cfg
done

# this needs for checking dpdk status, adding interfaces to dpdk, bind, unbind etc..

# Add hostname to /etc/hosts.
# Allow console access via pwd
cat <<EOF >/etc/cloud/cloud.cfg.d/10_etc_hosts.cfg
manage_etc_hosts: True
password: RANDOM
chpasswd: { expire: False }
ssh_pwauth: True
EOF

linuxheadersversion=$(echo ls boot/vmlinuz* | cut -d- -f2-)

apt-get update
apt-get install -y \
    bc \
    fio \
    gcc \
    git \
    iperf3 \
    iproute2 \
    ethtool \
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
    linux-headers-"${linuxheadersversion}" \
    libpcap-dev \
    lua5.2

# Build dpdk vPE VNF
pushd .
install_dpdk
popd .
git clone http://dpdk.org/git/dpdk
git clone http://dpdk.org/git/apps/pktgen-dpdk

CLONE_DEST=/opt/tempT
# remove before cloning
rm -rf -- "${CLONE_DEST}"
git clone https://github.com/kdlucas/byte-unixbench.git "${CLONE_DEST}"
make --directory "${CLONE_DEST}/UnixBench/"

git clone https://github.com/beefyamoeba5/ramspeed.git "${CLONE_DEST}/RAMspeed"
cd "${CLONE_DEST}/RAMspeed/ramspeed-2.6.0"
mkdir temp
bash build.sh

git clone https://github.com/beefyamoeba5/cachestat.git "${CLONE_DEST}"/Cachestat

# restore symlink
ln -sfrT /run/resolvconf/resolv.conf /etc/resolv.conf
