#!/bin/bash
##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# install tools
apt-get update && apt-get install -y \
    wget \
    expect \
    curl \
    git \
    sshpass \
    qemu-utils \
    kpartx \
    libffi-dev \
    libssl-dev \
    python \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    nginx \
    uwsgi \
    uwsgi-plugin-python \
    supervisor \
    python-setuptools && \
    easy_install -U setuptools

apt-get -y autoremove && apt-get clean


# fit for arm64
source_file=/etc/apt/sources.list
sed -i -e 's/^deb \([^/[]\)/deb [arch=amd64] \1/g' "${source_file}"
sed -i -e 's/^deb-src /# deb-src /g' "${source_file}"

sub_source_file=/etc/apt/sources.list.d/yardstick.list
touch "${sub_source_file}"
echo -e "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty main universe multiverse restricted
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-updates main universe multiverse restricted
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-security main universe multiverse restricted
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-proposed main universe multiverse restricted" > "${sub_source_file}"
echo "vm.mmap_min_addr = 0" > /etc/sysctl.d/mmap_min_addr.conf
dpkg --add-architecture arm64
apt-get install -y qemu-user-static libc6:arm64

# install yardstick + dependencies
easy_install -U pip
pip install -r requirements.txt
pip install .
