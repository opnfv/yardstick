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
ENV REPOS_DIR="/home/opnfv/repos" \
    IMAGE_DIR="/home/opnfv/images/"

# Set work directory

# Yardstick repo
ENV YARDSTICK_REPO_DIR="${REPOS_DIR}/yardstick" \
    STORPERF_REPO_DIR="${REPOS_DIR}/storperf"

RUN apt-get update && apt-get install -y git python-setuptools python-pip && apt-get -y autoremove && apt-get clean
RUN easy_install -U setuptools==30.0.0
RUN pip install appdirs==1.4.0 pyopenssl==17.5.0 python-openstackclient==3.11.0 python-heatclient==1.11.0

RUN mkdir -p ${REPOS_DIR}

RUN git config --global http.sslVerify false
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/storperf ${STORPERF_REPO_DIR}

WORKDIR ${YARDSTICK_REPO_DIR}
RUN ${YARDSTICK_REPO_DIR}/install.sh
RUN ${YARDSTICK_REPO_DIR}/docker/supervisor.sh

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# nginx=5000, rabbitmq=5672
EXPOSE 5000 5672

ADD http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img ${IMAGE_DIR}
ADD http://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img ${IMAGE_DIR}

COPY ./exec_tests.sh /usr/local/bin/

ENV NSB_DIR="/opt/nsb_bin" \
    PYTHONPATH="${PYTHONPATH}:${NSB_DIR}/trex_client:${NSB_DIR}/trex_client/stl"

WORKDIR ${REPOS_DIR}
CMD ["/usr/bin/supervisord"]
