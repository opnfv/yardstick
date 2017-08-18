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

ARG BRANCH=master
ARG NSB_BIN_DIR=/opt/nsb_bin

# GIT repo directory
ENV REPOS_DIR /home/opnfv/repos
ENV IMAGE_DIR /home/opnfv/images/

# Set work directory

# Yardstick repo
ENV YARDSTICK_REPO_DIR ${REPOS_DIR}/yardstick
ENV RELENG_REPO_DIR ${REPOS_DIR}/releng
ENV STORPERF_REPO_DIR ${REPOS_DIR}/storperf

RUN apt-get update && apt-get install -y git python-setuptools python-pip
RUN easy_install -U setuptools==30.0.0
RUN pip install appdirs==1.4.0

RUN mkdir -p ${REPOS_DIR} ${NSB_BIN_DIR}

RUN git config --global http.sslVerify false
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}
RUN git clone --depth 1 https://gerrit.opnfv.org/gerrit/releng ${RELENG_REPO_DIR}
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/storperf ${STORPERF_REPO_DIR}

WORKDIR ${YARDSTICK_REPO_DIR}
RUN ${YARDSTICK_REPO_DIR}/install.sh
RUN ${YARDSTICK_REPO_DIR}/docker/supervisor.sh

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

EXPOSE 5000

ADD http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img ${IMAGE_DIR}
ADD http://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img ${IMAGE_DIR}

COPY ./exec_tests.sh /usr/local/bin/

# copy TRex client API library
ARG TREX_VERSION=v2.28
ARG TREX_TMP_PATH=/tmp/trex
ARG TREX_WEB_URL=http://trex-tgn.cisco.com/trex/release
ENV TREX_CLIENT_LIB=${NSB_BIN_DIR}/trex_client/stl
RUN mkdir "$TREX_TMP_PATH" && wget -nv --no-cache "$TREX_WEB_URL/$TREX_VERSION.tar.gz" -P "$TREX_TMP_PATH" \
    && tar -C "$TREX_TMP_PATH" -xvf "$TREX_TMP_PATH/$TREX_VERSION.tar.gz" \
    && tar -C $NSB_BIN_DIR -xvf "$TREX_TMP_PATH/$TREX_VERSION/trex_client_$TREX_VERSION.tar.gz" \
    && rm "$TREX_TMP_PATH/$TREX_VERSION.tar.gz" && rm "$TREX_TMP_PATH/$TREX_VERSION/trex_client_$TREX_VERSION.tar.gz"

WORKDIR ${REPOS_DIR}
CMD ["/usr/bin/supervisord"]
