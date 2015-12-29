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

RUN apt-get update && apt-get install -y \
    wget \
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

ADD http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img /home/opnfv/images/

COPY ./run_tests.sh /usr/local/bin/

