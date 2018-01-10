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

set -e

INSTALL_OVS_BIN="/usr/src"
cd $INSTALL_OVS_BIN

if [[ $EUID -ne 0 ]]; then
  echo "Must be root to run $0"
  exit 1;
fi

download_zip()
{
  url=$1
  download_type=$2
  if [ -n "${download_type}" ]; then
    echo "Download ${download_type} zip"
  fi
  # rm goes into calling code
  echo "${url}"
  if [ ! -e "${url##*/}" ]; then
    wget "${url}"
  fi
  tar xvf "${url##*/}"
}

dpdk_build()
{
  echo "Build DPDK libraries"
  pushd .
  if [[ $DPDK_VERSION != "" ]]; then
    export DPDK_DIR=$INSTALL_OVS_BIN/dpdk-stable-$DPDK_VERSION
    export RTE_TARGET=x86_64-native-linuxapp-gcc
    export DPDK_BUILD=$DPDK_DIR/$RTE_TARGET
    rm -rf "$DPDK_DIR"
    DPDK_DOWNLOAD="http://fast.dpdk.org/rel/dpdk-$DPDK_VERSION.tar.xz"
    download_zip "${DPDK_DOWNLOAD}" "DPDK"
    cd dpdk-stable-"$DPDK_VERSION"
    make config T=$RTE_TARGET
    make install -j $(nproc) T=$RTE_TARGET
  fi
  popd
}

ovs()
{
  echo "Build and install OVS with DPDK"
  pushd .
  if [[ $OVS_VERSION != "" ]]; then
    rm -rf openswitch-"$OVS_VERSION"
    OVS_DOWNLOAD="http://openvswitch.org/releases/openvswitch-$OVS_VERSION.tar.gz"
    download_zip "${OVS_DOWNLOAD}" "OVS"
    cd openvswitch-"$OVS_VERSION"
    export OVS_DIR=/usr/src/openvswitch-$OVS_VERSION
    ./boot.sh
    if [[ $DPDK_VERSION != "" ]]; then
      ./configure --with-dpdk="$DPDK_BUILD"
    else
      ./configure
    fi
    make install -j $(nproc)
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
      echo "1. ovs_dpdk install mode:"
      echo "./ovs_install.sh --ovs=<2.7.0> --dpdk=<supported dpdk versoin for given ovs> -p=<proxy>"
      echo
      exit
    ;;
    *)
    ;;
  esac
done

main
