##############################################################################
# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM ubuntu:16.04

LABEL image=opnfv/yardstick-image-k8s

ARG BRANCH=master

# GIT repo directory
ENV CLONE_DEST="/opt/tempT"

RUN apt-get update && apt-get install -y \
  git bc bonnie++ fio gcc iperf3 ethtool \
  iproute2 linux-tools-common linux-tools-generic \
  lmbench make netperf patch perl rt-tests stress \
  sysstat iputils-ping openssh-server sudo && \
  apt-get -y autoremove && apt-get clean

RUN rm -rf -- ${CLONE_DEST}
RUN git clone https://github.com/kdlucas/byte-unixbench.git ${CLONE_DEST}
RUN mkdir -p ${CLONE_DEST}/UnixBench/

RUN git clone https://github.com/beefyamoeba5/ramspeed.git ${CLONE_DEST}/RAMspeed
WORKDIR ${CLONE_DEST}/RAMspeed/ramspeed-2.6.0
RUN mkdir -p ${CLONE_DEST}/RAMspeed/ramspeed-2.6.0/temp
RUN bash build.sh

RUN git clone https://github.com/beefyamoeba5/cachestat.git ${CLONE_DEST}/Cachestat

WORKDIR /

CMD /bin/bash
