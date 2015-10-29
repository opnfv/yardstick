##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM ubuntu:14.04

LABEL image=opnfv/yardstick-ci

# Yardstick repo location
ENV YARDSTICK_REPO_DIR /home/opnfv/yardstick

# Other repos (e.g. releng), not yardstick
ENV REPOS_DIR /home/opnfv/repos

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
    python-setuptools && \
    easy_install -U setuptools

RUN apt-get -y autoremove && \
    apt-get clean

RUN mkdir -p ${REPOS_DIR}

RUN git clone https://gerrit.opnfv.org/gerrit/yardstick ${YARDSTICK_REPO_DIR}

COPY ./run_benchmarks /usr/local/bin/
