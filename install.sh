#!/bin/bash
##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# fit for arm64
source_file=/etc/apt/sources.list
sed -i -e 's/^deb \([^/[]\)/deb [arch=amd64] \1/g' "${source_file}"
sed -i -e 's/^deb-src /# deb-src /g' "${source_file}"
echo "APT::Default-Release \"trusty\";" > /etc/apt/apt.conf.d/default-distro

sub_source_file=/etc/apt/sources.list.d/yardstick.list
touch "${sub_source_file}"
echo -e "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ xenial-updates universe
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty main universe multiverse restricted
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-updates main universe multiverse restricted
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-security main universe multiverse restricted
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-proposed main universe multiverse restricted" > "${sub_source_file}"
echo "vm.mmap_min_addr = 0" > /etc/sysctl.d/mmap_min_addr.conf
dpkg --add-architecture arm64

# install tools
apt-get update && apt-get install -y \
    qemu-user-static/xenial \
    libc6:arm64 \
    wget \
    expect \
    curl \
    git \
    sshpass \
    qemu-utils \
    kpartx \
    libffi-dev \
    libssl-dev \
    libzmq-dev \
    python \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    nginx \
    uwsgi \
    uwsgi-plugin-python \
    supervisor \
    python-pip \
    vim \
    python-setuptools && \
    easy_install -U setuptools==30.0.0

apt-get -y autoremove && apt-get clean

git config --global http.sslVerify false


# install yardstick + dependencies
easy_install -U pip
pip install -r requirements.txt
pip install .

/bin/bash "$(pwd)/api/api-prepare.sh"

service nginx restart
uwsgi -i /etc/yardstick/yardstick.ini
