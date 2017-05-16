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
DOCKER_ARCH="$(uname -m)"

UBUNTU_PORTS_URL="http://ports.ubuntu.com/ubuntu-ports"
UBUNTU_ARCHIVE_URL="http://archive.ubuntu.com/ubuntu/"

source_file=/etc/apt/sources.list

if [[ "${DOCKER_ARCH}" == "aarch64" ]]; then
    sed -i -e 's/^deb \([^/[]\)/deb [arch=arm64] \1/g' "${source_file}"
    DOCKER_ARCH="arm64"
    DOCKER_REPO="${UBUNTU_PORTS_URL}"
    EXTRA_ARCH="amd64"
    EXTRA_REPO="${UBUNTU_ARCHIVE_URL}"
else
    sed -i -e 's/^deb \([^/[]\)/deb [arch=amd64] \1/g' "${source_file}"
    DOCKER_ARCH="amd64"
    DOCKER_REPO="${UBUNTU_ARCHIVE_URL}"
    EXTRA_ARCH="arm64"
    EXTRA_REPO="${UBUNTU_PORTS_URL}"
    dpkg --add-architecture arm64
fi

sed -i -e 's/^deb-src /# deb-src /g' "${source_file}"
echo "APT::Default-Release \"trusty\";" > /etc/apt/apt.conf.d/default-distro

sub_source_file=/etc/apt/sources.list.d/yardstick.list
touch "${sub_source_file}"

# first add xenial repo needed for installing qemu_static_user/xenial in the container
# then add complementary architecture repositories in case the cloud image is of different arch
echo -e "deb [arch="${DOCKER_ARCH}"] "${DOCKER_REPO}" xenial-updates universe
deb [arch="${EXTRA_ARCH}"] "${EXTRA_REPO}" trusty main universe multiverse restricted
deb [arch="${EXTRA_ARCH}"] "${EXTRA_REPO}" trusty-updates main universe multiverse restricted
deb [arch="${EXTRA_ARCH}"] "${EXTRA_REPO}" trusty-security main universe multiverse restricted
deb [arch="${EXTRA_ARCH}"] "${EXTRA_REPO}" trusty-proposed main universe multiverse restricted" > "${sub_source_file}"

echo "vm.mmap_min_addr = 0" > /etc/sysctl.d/mmap_min_addr.conf

# install tools
apt-get update && apt-get install -y \
    qemu-user-static/xenial \
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
    vim

if [[ "${DOCKER_ARCH}" != "aarch64" ]]; then
    apt-get install -y libc6:arm64
fi

apt-get -y autoremove && apt-get clean

git config --global http.sslVerify false


# install yardstick + dependencies
easy_install -U pip
pip install -r requirements.txt
pip install -e .

/bin/bash "$(pwd)/api/api-prepare.sh"

service nginx restart
uwsgi -i /etc/yardstick/yardstick.ini
