##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM ubuntu:14.04
MAINTAINER Hans Feldt <hans.feldt@ericsson.com>

# TODO: Is there some easy way to get the fastest/closest mirror?
#RUN sed -i 's/archive.ubuntu.com/ftp.acc.umu.se/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    python \
    python-dev \
    python-setuptools && \
    easy_install -U setuptools

COPY . /tmp/yardstick

RUN cd /tmp/yardstick && \
    python setup.py install && \
    apt-get -y remove \
        binutils \
        cpp \
        gcc \
        libffi-dev \
        libssl-dev \
        python3 \
        python-dev && \
    apt-get -y autoremove && \
    apt-get clean && \
    useradd -u 65500 -m yardstick && \
    cp -a samples /home/yardstick && \
    chown -R yardstick /home/yardstick/samples && \
    chgrp -R yardstick /home/yardstick/samples && \
    rm -rf /tmp/* && \
    rm -rf /var/lib/apt/lists/*

USER yardstick
CMD bash --login
ENV HOME /home/yardstick
WORKDIR /home/yardstick
