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

echo "Install required libraries to run collectd..."
pkg=(git flex bison build-essential pkg-config automake  autotools-dev libltdl-dev librabbitmq-dev rabbitmq-server)
for i in "${pkg[@]}"; do
dpkg-query -W --showformat='${Status}\n' "${i}"|grep "install ok installed"
    if [  "$?" -eq "1" ]; then
        apt-get -y install "${i}";
    fi
done
echo "Done"

ldconfig -p | grep libpqos >/dev/null
if [ $? -eq 0 ]
then
    echo "Intel RDT library already installed. Done"
else
    pushd .

    echo "Get intel_rdt repo and install..."
    rm -rf intel-cmt-cat >/dev/null
    git clone https://github.com/01org/intel-cmt-cat.git
    pushd intel-cmt-cat
    git checkout tags/v1.5 -b v1.5
    make install PREFIX=/usr
    popd

    popd
    echo "Done."
fi

which /opt/nsb_bin/collectd/collectd >/dev/null
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
    git checkout -b collectd 43a4db3b3209f497a0ba408aebf8aee385c6262d
    ./build.sh
    ./configure --with-libpqos=/usr/
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
