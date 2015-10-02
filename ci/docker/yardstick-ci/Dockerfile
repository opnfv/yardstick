##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM ubuntu:14.04

RUN apt-get update && apt-get install -y \
    wget \
    git \
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

RUN echo "ALL ALL=NOPASSWD: ALL" > /etc/sudoers.d/open-sudo
RUN chmod 0440 /etc/sudoers.d/open-sudo

RUN git clone https://gerrit.opnfv.org/gerrit/yardstick /home/yardstick

COPY ./run_yardstick /usr/local/bin/
#COPY ./openrc /home/yardstick/ci/
