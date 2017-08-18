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
INSTALL_NSB_BIN="/opt/nsb_bin"
cd $INSTALL_NSB_BIN

if [ "$(whoami)" != "root" ]; then
        echo "Must be root to run $0"
        exit 1;
fi

echo "setup proxy..."
if [[ -n $1 ]]; then
    export http_proxy=$1
    export https_proxy=$2
fi

if [[ -n $2 ]]; then
    export https_proxy=$2
fi

echo "Install required libraries to run collectd..."
pkg=(git flex bison build-essential pkg-config automake  autotools-dev libltdl-dev librabbitmq-dev rabbitmq-server cmake libvirt-dev)
for i in "${pkg[@]}"; do
dpkg-query -W --showformat='${Status}\n' "${i}"|grep "install ok installed"
    if [  "$?" -eq "1" ]; then
        apt-get -y install "${i}";
    fi
done
echo "Done"

if ldconfig -p | grep -q libpqos ; then
    echo "Intel RDT library already installed. Done"
else
    pushd .

    echo "Get intel_rdt repo and install..."
    rm -rf intel-cmt-cat >/dev/null
    git clone https://github.com/01org/intel-cmt-cat.git

    (cd intel-cmt-cat; make install PREFIX=/usr)

    popd
    echo "Done."
fi

if [[ -r /usr/lib/libdpdk.so ]]; then
    echo "DPDK already installed. Done"
else
    pushd .

    echo "Get dpdk and install..."
    mkdir -p $INSTALL_NSB_BIN
    pushd dpdk-16.07
    mkdir -p /mnt/huge
    mount -t hugetlbfs nodev /mnt/huge
    sed -i 's/CONFIG_RTE_BUILD_SHARED_LIB=n/CONFIG_RTE_BUILD_SHARED_LIB=y/g' config/common_base
    sed -i 's/CONFIG_RTE_EAL_PMD_PATH=""/CONFIG_RTE_EAL_PMD_PATH="\/usr\/lib\/dpdk-pmd\/"/g' config/common_base

                echo "Build dpdk v16.07"
                make config T=x86_64-native-linuxapp-gcc
                make
                sudo make install prefix=/usr
                mkdir -p /usr/lib/dpdk-pmd
                find /usr/lib -type f -name 'librte_pmd*' | while read path ; do ln -s $path /usr/lib/dpdk-pmd/`echo $path | grep -o 'librte_.*so'` ;  done

                echo "Disable ASLR."
                echo 0 > /proc/sys/kernel/randomize_va_space
    make install PREFIX=/usr
    popd

    popd
    echo "Done."
fi

which $INSTALL_NSB_BIN/yajl > /dev/null
if [ -f "/usr/local/lib/libyajl.so.2.1.1" ]
then
                                echo "ovs stats libs already installed."
else
                echo "installing ovs stats libraries"
                pushd .

                cd $INSTALL_NSB_BIN
                git clone https://github.com/lloyd/yajl.git
                pushd yajl
                ./configure
                make
                make install
                popd

    popd
fi

which $INSTALL_NSB_BIN/collectd/collectd >/dev/null
if [ $? -eq 0 ]
then
    echo "Collectd already installed. Done"
else
    pushd .
    echo "Get collectd from repository and install..."
    rm -rf collectd >/dev/null
    git clone https://github.com/collectd/collectd.git
    pushd collectd
    git stash
    git checkout -b nfvi 47c86ace348a1d7a5352a83d10935209f89aa4f5
    ./build.sh
    ./configure --with-libpqos=/usr/ --with-libdpdk=/usr --with-libyajl=/usr/local --enable-debug --enable-dpdkstat --enable-virt --enable-ovs_stats
    make install > /dev/null
    popd
    echo "Done."
    popd
fi

modprobe msr
cp $INSTALL_NSB_BIN/collectd.conf /opt/collectd/etc/

echo "Check if admin user already created"
rabbitmqctl list_users | grep '^admin$' > /dev/null
if [ $? -eq 0 ];
then
    echo "'admin' user already created..."
else
    echo "Creating 'admin' user for collectd data export..."
    rabbitmqctl delete_user guest
    rabbitmqctl add_user admin admin
    rabbitmqctl authenticate_user admin admin
    rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"
    echo "Done"
fi
