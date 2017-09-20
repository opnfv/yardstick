#!/bin/bash
#
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

INSTALL_OVS_BIN="/usr/src"
cd $INSTALL_OVS_BIN


if [ "$(whoami)" != "root" ]; then
        echo "Must be root to run $0"
        exit 1;
fi

prerequisite()
{
		echo "Install required libraries to run collectd..."
		pkg=(git flex bison build-essential pkg-config automake autotools-dev libltdl-dev cmake qemu-kvm libvirt-bin bridge-utils numactl libnuma-dev libpcap-dev)
		for i in "${pkg[@]}"; do
		dpkg-query -W --showformat='${Status}\n' "${i}"|grep "install ok installed"
						if [  "$?" -eq "1" ]; then
										apt-get update
										apt-get -y install "${i}";
						fi
		done
		echo "Done"
}

download_dpdk_zip()
{
	echo "Download DPDK zip"
	DPDK_DOWNLOAD="http://fast.dpdk.org/rel/dpdk-$DPDK_VERSION.tar.xz"
	rm -rf $DPDK_DIR
	echo $DPDK_DOWNLOAD
	if [ ! -e ${DPDK_DOWNLOAD##*/} ] ; then
		wget ${DPDK_DOWNLOAD}
	fi
	tar xvf  ${DPDK_DOWNLOAD##*/}
}

dpdk_build()
{
		pushd .
	 if [[ $DPDK_VERSION != "" ]]; then
    export DPDK_DIR=$INSTALL_OVS_BIN/dpdk-stable-$DPDK_VERSION
    export RTE_TARGET=x86_64-native-linuxapp-gcc
    export DPDK_BUILD=$DPDK_DIR/$RTE_TARGET
	 		download_dpdk_zip
    cd dpdk-stable-$DPDK_VERSION
    make install -j T=$RTE_TARGET
  fi
  popd
}

download_ovs_zip()
{
	echo "Download DPDK zip"
	OVS_DOWNLOAD="http://openvswitch.org/releases/openvswitch-$OVS_VERSION.tar.gz"
	rm -rf openvswitch-$OVS_VERSION
	echo $OVS_DOWNLOAD
	if [ ! -e ${OVS_DOWNLOAD##*/} ] ; then
		wget ${OVS_DOWNLOAD}
	fi
	tar xvf  ${OVS_DOWNLOAD##*/}
}

ovs()
{
		pushd .
	 if [[ $OVS_VERSION != "" ]]; then
	 		download_ovs_zip
    cd openvswitch-$OVS_VERSION
    export OVS_DIR=/usr/src/openvswitch-$OVS_VERSION

				./boot.sh
				if [[ $DPDK_VERSION != "" ]]; then
						./configure --with-dpdk=$DPDK_BUILD
				else
						./configure
				fi
				make install -j
  fi
  popd

}

main()
{
   dpdk_build
   ovs
}

for i in "$@"
do
case $i in
		-o=*|--ovs=*)
		OVS_VERSION="${i#*=}"
		;;
		-d=*|--dpdk=*)
		DPDK_VERSION="${i#*=}"
		;;
		-p=*|--proxy=*)
		export http_proxy="${i#*=}"
		export https_proxy="${i#*=}"
		;;
		-h|--help)
		echo "CommandLine options:"
		echo "===================="
		echo "1. ovs install mode:"
		echo "./ovs_install.sh --ovs=<2.7.0> --dpdk=<supported dpdk versoin for given ovs> -p=<proxy>"
		echo
		exit
		;;
		--default)
		INTERACTIVE=true
		;;
		*)
  ;;
esac
done

main	
