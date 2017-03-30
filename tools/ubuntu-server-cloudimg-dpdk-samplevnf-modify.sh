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
TREX_VERSION="v2.20"
TREX_DOWNLOAD="https://trex-tgn.cisco.com/trex/release/$TREX_VERSION.tar.gz"
TREX_DIR=$INSTALL_BIN_PATH/trex/scripts

enable_proxy()
{
       echo $https_proxy
       echo $http_proxy
       if [[ "$http_proxy" != "" ]]; then
           echo 'Acquire::http::Proxy "$http_proxy";' > /etc/apt/apt.conf
       fi
}

install_trex()
{

	INSTALL_BIN_PATH="/opt/nsb_bin"
	DPDK_DOWNLOAD="http://dpdk.org/browse/dpdk/snapshot/dpdk-16.07.zip"
	TREX_VERSION="v2.20"
	TREX_DOWNLOAD="https://trex-tgn.cisco.com/trex/release/$TREX_VERSION.tar.gz"
	TREX_DIR=$INSTALL_BIN_PATH/trex/scripts
        pushd .
	cd $INSTALL_BIN_PATH
	echo "Build TRex and installing Trex TG in $INSTALL_BIN_PATH/trex"
	rm -rf ${TREX_DOWNLOAD##*/}
	if [ ! -e ${TREX_DOWNLOAD##*/} ] ; then
	    wget $TREX_DOWNLOAD
	fi
	tar zxvf ${TREX_DOWNLOAD##*/}
	#pushd .
	rm -rf $INSTALL_BIN_PATH/trex
	mkdir -p $INSTALL_BIN_PATH/trex
	mv $TREX_VERSION trex/scripts
	rm -rf $TREX_VERSION.tar.gz
	cd $INSTALL_BIN_PATH/trex/scripts/ko/src/
	make
	make install
	touch "$INSTALL_BIN_PATH/trex/scripts/automation/trex_control_plane/stl/__init__.py"
	cp "$INSTALL_BIN_PATH/trex/scripts/dpdk_nic_bind.py" "$INSTALL_BIN_PATH"
        popd
}
install_sample_vnf()
{
	mkdir -p $INSTALL_BIN_PATH
        echo "Install Sample VNFs"
        pushd .
        cd $INSTALL_BIN_PATH
        git clone https://git.opnfv.org/samplevnf
        cd samplevnf
        VNF_CORE=$INSTALL_BIN_PATH/samplevnf
        ./tools/vnf_build.sh --silient '17.02'
        cp $VNF_CORE/VNFs/vACL/build/vACL $INSTALL_BIN_PATH
        cp $VNF_CORE/VNFs/vCGNAPT/build/vCGNAPT $INSTALL_BIN_PATH
        cp $VNF_CORE/VNFs/vFW/build/vFW $INSTALL_BIN_PATH
        cp $VNF_CORE/VNFs/DPPD-PROX/build/prox $INSTALL_BIN_PATH
        cp $VNF_CORE/VNFs/UDP_Replay/build/UDP_Replay $INSTALL_BIN_PATH

        # build vpe
        cd $VNF_CORE/dpdk/examples/ip_pipeline
        export RTE_SDK= $VNF_CORE/dpdk
        make
        cp $VNF_CORE/build/ip_pipeline $INSTALL_BIN_PATH/vPE_vnf

        cp -r $VNF_CORE/dpdk $INSTALL_BIN_PATH/dpdk
	echo "Done"
        popd
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

echo 'GRUB_CMDLINE_LINUX="resume=/dev/sda1 default_hugepagesz=1G hugepagesz=1G hugepages=4 iommu=on iommu=pt intel_iommu=on"' >> /etc/default/grub
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
#password: RANDOM
password: password
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
enable_proxy
install_sample_vnf
install_trex
popd .
cd /root

sed -i -e 's/PermitRootLogin without-password/PermitRootLogin yes/g'  /etc/ssh/sshd_config
sed -i -e 's/prohibit-password/yes/g' /etc/ssh/sshd_config
passwd

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
