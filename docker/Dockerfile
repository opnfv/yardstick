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
ARG NSB_BIN_DIR=/tmp/nsb_bin

# GIT repo directory
ENV REPOS_DIR /home/opnfv/repos
ENV IMAGE_DIR /home/opnfv/images/

# Set work directory

# Yardstick repo
ENV YARDSTICK_REPO_DIR ${REPOS_DIR}/yardstick
ENV RELENG_REPO_DIR ${REPOS_DIR}/releng

RUN apt-get update && apt-get install -y git python-setuptools python-pip redis-server
RUN easy_install -U setuptools==30.0.0
RUN pip install appdirs==1.4.0

RUN mkdir -p ${REPOS_DIR} ${NSB_BIN_DIR}

RUN git config --global http.sslVerify false
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}
RUN git config --global user.email "you@example.com"; git config --global user.name "Your Name"; cd ${YARDSTICK_REPO_DIR}; \
    git fetch https://gerrit.opnfv.org/gerrit/yardstick refs/changes/45/36745/3 && git cherry-pick FETCH_HEAD; \
    git fetch https://gerrit.opnfv.org/gerrit/yardstick refs/changes/47/36747/9 && git cherry-pick FETCH_HEAD; \
    git fetch https://gerrit.opnfv.org/gerrit/yardstick refs/changes/61/34861/17 && git cherry-pick FETCH_HEAD

RUN git clone --depth 1 https://gerrit.opnfv.org/gerrit/releng ${RELENG_REPO_DIR}

WORKDIR ${YARDSTICK_REPO_DIR}
RUN ${YARDSTICK_REPO_DIR}/install.sh

RUN cd ${YARDSTICK_REPO_DIR}/gui; pip install -r requirements.txt

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

EXPOSE 5000

ADD http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img ${IMAGE_DIR}
ADD http://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img ${IMAGE_DIR}

COPY ./exec_tests.sh /usr/local/bin/
COPY ./dpdk-devbind.py ${NSB_BIN_DIR}

# copy TRex client API library
ARG TREX_VERSION=v2.20
ARG TREX_TMP_PATH=/tmp/trex
ARG TREX_WEB_URL=http://trex-tgn.cisco.com/trex/release
ENV TREX_CLIENT_LIB=/opt/trex_client/stl
RUN mkdir "$TREX_TMP_PATH" && wget -nv --no-cache "$TREX_WEB_URL/$TREX_VERSION.tar.gz" -P "$TREX_TMP_PATH" \
&& tar -C "$TREX_TMP_PATH" -xvf "$TREX_TMP_PATH/$TREX_VERSION.tar.gz" \
&& tar -C /opt/ -xvf "$TREX_TMP_PATH/$TREX_VERSION/trex_client_$TREX_VERSION.tar.gz" \
&& rm "$TREX_TMP_PATH/$TREX_VERSION.tar.gz" && rm "$TREX_TMP_PATH/$TREX_VERSION/trex_client_$TREX_VERSION.tar.gz"

WORKDIR ${REPOS_DIR}
CMD ["/usr/bin/supervisord"]
