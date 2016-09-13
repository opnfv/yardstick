##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM ubuntu:14.04

LABEL image=opnfv/yardstick

# GIT repo directory
ENV REPOS_DIR /home/opnfv/repos

# Yardstick repo
ENV YARDSTICK_REPO_DIR ${REPOS_DIR}/yardstick
ENV RELENG_REPO_DIR ${REPOS_DIR}/releng
RUN sed -i -e 's/^deb /deb [arch=amd64] /g' /etc/apt/sources.list
RUN sed -i -e 's/^deb-src /# deb-src /g' /etc/apt/sources.list
RUN echo "\n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty main universe multiverse restricted \n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-updates main universe multiverse restricted \n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-security main universe multiverse restricted \n\
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-proposed main universe multiverse restricted" >> /etc/apt/sources.list
RUN echo "vm.mmap_min_addr = 0" > /etc/sysctl.d/mmap_min_addr.conf
RUN dpkg --add-architecture arm64

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
    python \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    python-setuptools && \
    easy_install -U setuptools

RUN apt-get -y autoremove && \
    apt-get clean

RUN mkdir -p ${REPOS_DIR}

RUN git config --global http.sslVerify false
RUN git clone https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}
RUN git clone https://gerrit.opnfv.org/gerrit/releng ${RELENG_REPO_DIR}

# install yardstick + dependencies
RUN cd ${YARDSTICK_REPO_DIR} && easy_install -U pip
RUN cd ${YARDSTICK_REPO_DIR} && pip install -r tests/ci/requirements.txt
RUN cd ${YARDSTICK_REPO_DIR} && pip install .

COPY ./exec_tests.sh /usr/local/bin/
