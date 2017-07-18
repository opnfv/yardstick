##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM ubuntu:16.04

LABEL image=opnfv/yardstick

ARG BRANCH=master

# GIT repo directory
ENV REPOS_DIR /home/opnfv/repos

# Yardstick repo
ENV YARDSTICK_REPO_DIR ${REPOS_DIR}/yardstick
ENV RELENG_REPO_DIR ${REPOS_DIR}/releng
RUN sed -i -e 's/^deb /deb [arch=amd64] /g;s/^deb-src /# deb-src /g' /etc/apt/sources.list && \
    echo "\n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty main universe multiverse restricted \n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-updates main universe multiverse restricted \n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-security main universe multiverse restricted \n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-proposed main universe multiverse restricted" >> /etc/apt/sources.list && \
    dpkg --add-architecture arm64

# WHY? Is this workaround still needed?
# https://wiki.debian.org/mmap_min_addr#apps
# qemu, as shipped in Debian 5.0, requires low virtual memory mmaps. mmap_min_addr must be set to 0 to run qemu as a non-root user. This limitation has been removed upstream, so qemu should work with an increased mmap_min_addr starting with Debian squeeze.
#RUN echo "vm.mmap_min_addr = 0" > /etc/sysctl.d/mmap_min_addr.conf

# This will prevent questions from being asked during the install
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    qemu-user-static \
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
    python-setuptools && \
    easy_install -U setuptools==30.0.0 && \
    apt-get -y autoremove && \
    apt-get clean

RUN mkdir -p ${REPOS_DIR} && \
    git config --global http.sslVerify false && \
    git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}  && \
    git clone --depth 1 https://gerrit.opnfv.org/gerrit/releng ${RELENG_REPO_DIR}

# install yardstick + dependencies
# explicity pin pip version to avoid future issues like the ill-fated pip 8.0.0 release
RUN easy_install -U "pip==${PIP_VERSION}" && \
    pip install -r ${YARDSTICK_REPO_DIR}/requirements.txt && \
    pip install ${YARDSTICK_REPO_DIR}

RUN ${YARDSTICK_REPO_DIR}/api/api-prepare.sh

EXPOSE 5000

ADD http://download.cirros-cloud.net/0.3.3/cirros-0.3.5-x86_64-disk.img /home/opnfv/images/
ADD http://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img /home/opnfv/images/

COPY ./exec_tests.sh /usr/local/bin/
CMD ["/usr/bin/supervisord"]
