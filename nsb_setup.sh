#! /bin/bash
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

#
# Change to yardstick directory ( <current-dir>/.. ), and export it as REPO_DIR
#
cd "$(dirname "${BASH_SOURCE[0]}")"
export REPO_DIR=$PWD
echo "------------------------------------------------------------------------------"
echo " REPO_DIR exported as $REPO_DIR"
echo "------------------------------------------------------------------------------"

if [ "$(whoami)" != "root" ]; then
    echo "Must be root to run $0"
    exit 1;
fi

INSTALL_BIN_PATH="/opt/nsb_bin"
TREX_VERSION="v2.28"
TREX_DOWNLOAD="https://trex-tgn.cisco.com/trex/release/$TREX_VERSION.tar.gz"
DPDK_DOWNLOAD="http://dpdk.org/browse/dpdk/snapshot/dpdk-16.07.zip"
VIRTUAL_VENV="$INSTALL_BIN_PATH/yardstick_venv"

#
# Install libs needed for NSB
#
install_libs()
{
    echo "Install libs needed to build and run NSB Testing..."
    apt-get update > /dev/null 2>&1
    pkg=(git build-essential python-dev virtualenv python-virtualenv virtualenv linux-headers-$(uname -r) unzip  python-pip libpcap-dev cmake)
    for i in "${pkg[@]}"; do
    dpkg-query -W --showformat='${Status}\n' "${i}"|grep "install ok installed"
    if [  "$?" -eq "1" ]; then
        apt-get -y install "${i}";
    fi
    done
    echo "Done"
}

install_yardstick()
{
    echo "Create install directory... $INSTALL_BIN_PATH"
    mkdir -p $INSTALL_BIN_PATH
    echo "Install yardstick dependencies and build Yardstick in venv..."
    pushd .
    rm -rf $VIRTUAL_VENV
    echo $VIRTUAL_VENV
    virtualenv $VIRTUAL_VENV
    if [ ! -f "$INSTALL_BIN_PATH/yardstick_venv/bin/activate" ]; then
         echo "Installation Error. Failed to create yardstick virtual env..."
         exit 1
    fi
    source $VIRTUAL_VENV/bin/activate
    bash ./install.sh
    python setup.py install
    popd

    pushd .
    echo "Copying yardstick sample conf & pod file to /etc/yardstick/nodes"
    mkdir -p /etc/yardstick/nodes
    cp "$REPO_DIR/etc/yardstick/yardstick.conf.sample" "/etc/yardstick/yardstick.conf"
    cp "$REPO_DIR/etc/yardstick/nodes/pod.yaml.nsb.sample" "/etc/yardstick/nodes/"
    popd
}

#
# Install trex for TH setup
#
install_trex()
{
    TREX_DIR=$INSTALL_BIN_PATH/trex/scripts
    if [ -d "$TREX_DIR" ]; then
        echo "Trex $TREX_VERSION already installed."
    else
        echo "Build TRex and installing Trex TG in $INSTALL_BIN_PATH/trex"
        rm -rf ${TREX_DOWNLOAD##*/}
        if [ ! -e ${TREX_DOWNLOAD##*/} ] ; then
            wget $TREX_DOWNLOAD
        fi
        tar zxvf ${TREX_DOWNLOAD##*/}
        pushd .
        rm -rf trex
        mkdir -p trex
        mv $TREX_VERSION trex/scripts
        rm -rf $TREX_VERSION.tar.gz
        cd trex/scripts/ko/src/
        make
        make install
        ln -s $TREX_DIR/automation/trex_control_plane $INSTALL_BIN_PATH/trex_client
        popd
    fi
    echo "Done."
}

install_dpdk()
{
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
        Pages=16
        if [[ "$HUGEPGSZ" = "2048kB" ]] ; then
            Pages=16384
        fi
        grep nr_hugepages /etc/sysctl.conf
        if [[ "$?" -eq '1' ]] ; then
            sh -c "echo 'vm.nr_hugepages=$Pages' >> /etc/sysctl.conf"
        fi
            echo "echo $Pages > /sys/kernel/mm/hugepages/hugepages-${HUGEPGSZ}/nr_hugepages" > .echo_tmp
            echo "Reserving hugepages"
            sudo sh .echo_tmp
            rm -f .echo_tmp

            service procps start
            echo "Creating /mnt/huge and mounting as hugetlbfs"
            sudo mkdir -p /mnt/huge

            grep -s '/mnt/huge' /proc/mounts > /dev/null
            if [ $? -ne 0 ] ; then
                sudo mount -t hugetlbfs nodev /mnt/huge
            fi
            popd
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


push_nsb_binary()
{
    if [ ! -d "$INSTALL_BIN_PATH/trex/scripts" ]; then
        cp -fr "$REPO_DIR/trex" "$INSTALL_BIN_PATH"
    fi
    rm -rf "$REPO_DIR/trex"

    if [ -d "$INSTALL_BIN_PATH/trex" ]; then
        echo "Setup Environment variables for Test Harness...."
        PYTHONPATH="$INSTALL_BIN_PATH/trex/scripts/automation/trex_control_plane:$INSTALL_BIN_PATH/trex/scripts/automation/trex_control_plane/stl"
        PY_PATH=$(grep PYTHONPATH ~/.bash_profile)
        if [ "$PY_PATH" = "" ] ; then
            sh -c "echo export PYTHONPATH=$PYTHONPATH >> ~/.bash_profile" > /dev/null
        else
            echo "Your ~/.bash_profile already contains a PYTHONPATH definition."
            echo "Make sure it contains $PYTHONPATH which is required to run TRex"
        fi
    fi
    cp "$REPO_DIR/yardstick/network_services/nfvi/collectd.sh" "$INSTALL_BIN_PATH"
    cp "$REPO_DIR/yardstick/network_services/nfvi/collectd.conf" "$INSTALL_BIN_PATH"
    cp "$REPO_DIR/nsb_setup.sh" "$INSTALL_BIN_PATH"

    # Get "dpdk-devbind.py" to find the ports for VNF to run
    wget http://dpdk.org/browse/dpdk/plain/usertools/dpdk-devbind.py?h=v17.05 -O dpdk-devbind.py
    chmod 777 dpdk-devbind.py
    mv dpdk-devbind.py "$INSTALL_BIN_PATH"
    ln "$INSTALL_BIN_PATH"/dpdk-devbind.py "$INSTALL_BIN_PATH"/dpdk_nic_bind.py
    echo "Done"
}

check_installed_files()
{
    if [ ! -f "$INSTALL_BIN_PATH/yardstick_venv/bin/activate" ]; then
        echo "Installation Error. Failed to create yardstick virtual env..."
        exit 1
    fi

    if [ ! -d "$INSTALL_BIN_PATH/dpdk-16.07" ]; then
        echo "Installation Error. Failed to download and install dpdk-16.07..."
        exit 1
    fi

    if [ ! -d "$INSTALL_BIN_PATH/trex" ]; then
        echo "Installation Error. Failed to download and configure Trex"
        exit 1
    fi

    if [ ! -f "$INSTALL_BIN_PATH/vPE_vnf" ]; then
        echo "Installation Error. vPE VNF not present in install dir $INSTALL_BIN_PATH"
        exit 1
    fi
}

if [ "$1" == "dpdk" ]; then
   install_libs
   install_dpdk
else
   install_libs
   install_yardstick
   install_dpdk
   install_trex
   push_nsb_binary
   check_installed_files
clear
echo "Installation completed..."
echo "Virtual Environment : $INSTALL_BIN_PATH/yardstick_venv"
echo "Please refer to Chapter 13 of the Yardstick User Guide for how to get started with VNF testing."
fi
