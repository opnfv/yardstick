##############################################################################
# Copyright (c) 2017 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM centos:7.3.1611

LABEL image=opnfv/yardstick

ARG BRANCH=master

# GIT repo directory
ENV REPOS_DIR /home/opnfv/repos

# Yardstick repo
ENV YARDSTICK_REPO_DIR ${REPOS_DIR}/yardstick
ENV RELENG_REPO_DIR ${REPOS_DIR}/releng

RUN yum -y install\
    deltarpm \
    wget \
    expect \
    curl \
    git \
    sshpass \
    ansible \
    qemu-kvm \
    qemu-utils \
    kpartx \
    libffi-devel \
    openssl-devel \
    zeromq2-devel \
    python \
    python-devel \
    libxml2-devel \
    libxslt-devel \
    nginx \
    uwsgi \
    uwsgi-plugin-python \
    supervisor \
    ansible \
    python-setuptools && \
    easy_install -U setuptools==30.0.0 && \
    yum clean all

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

ADD http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img /home/opnfv/images/
ADD http://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img /home/opnfv/images/

COPY ./exec_tests.sh /usr/local/bin/
CMD ["/usr/bin/supervisord"]
