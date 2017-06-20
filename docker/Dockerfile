##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
# Copyright (c) 2017 Enea AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM aarch64/ubuntu:14.04
# x86_64 note: please use dockerfile in ../ansible/roles/create_dockerfile/templates/ubuntu/

LABEL image=opnfv/yardstick_aarch64

ARG BRANCH=master

# GIT repo directory
ENV REPOS_DIR /home/opnfv/repos
ENV IMAGE_DIR /home/opnfv/images/

# Set work directory

# Yardstick repo
ENV YARDSTICK_REPO_DIR ${REPOS_DIR}/yardstick
ENV RELENG_REPO_DIR ${REPOS_DIR}/releng
ENV STORPERF_REPO_DIR ${REPOS_DIR}/storperf

# http proxy settings
#ENV https_proxy=''
#ENV http_proxy=''

# Setup proper env
ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C
# noninteractive will prevent questions from being asked during the install
RUN  apt-get update && apt-get install -y git python-setuptools python-pip && apt-get -y autoremove && apt-get clean
RUN easy_install -U setuptools==30.0.0
RUN pip install appdirs==1.4.0

RUN mkdir -p ${REPOS_DIR}

RUN git config --global http.sslVerify false
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}
RUN git clone --depth 1 https://gerrit.opnfv.org/gerrit/releng ${RELENG_REPO_DIR}
RUN git clone --depth 1 -b $BRANCH https://gerrit.opnfv.org/gerrit/storperf ${STORPERF_REPO_DIR}
RUN for i in ${YARDSTICK_REPO_DIR} ${RELENG_REPO_DIR} ${STORPERF_REPO_DIR}; do \
        rm -r "${i}/.git"; \
    done

WORKDIR ${YARDSTICK_REPO_DIR}
RUN ${YARDSTICK_REPO_DIR}/install.sh
RUN ${YARDSTICK_REPO_DIR}/docker/supervisor.sh

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

EXPOSE 5000

ADD http://download.cirros-cloud.net/daily/20161201/cirros-d161201-aarch64-disk.img ${IMAGE_DIR}
ADD http://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-arm64-disk1.img ${IMAGE_DIR}


COPY ./exec_tests.sh /usr/local/bin/

WORKDIR ${REPOS_DIR}
CMD ["/usr/bin/supervisord"]
