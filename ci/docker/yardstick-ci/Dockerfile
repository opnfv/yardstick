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
    qemu-utils \
    kpartx \
    libffi-dev \
    libssl-dev \
    python \
    python-dev \
    python-setuptools \
    python-pip && \
    apt-get -y autoremove && \
    apt-get clean && \
    easy_install -U setuptools && \
    pip install --upgrade pip && \
    pip install 'pbr<2.0,>=1.3' && \
    pip install 'Jinja2>=2.6' && \
    pip install 'PyYAML>=3.10' && \
    pip install 'python-glanceclient>=0.12.0' && \
    pip install 'python-heatclient>=0.2.12' && \
    pip install 'python-keystoneclient>=0.11.1' && \
    pip install 'python-neutronclient>=2.3.9' && \
    pip install 'python-novaclient>=2.24.1' 

RUN echo "ALL ALL=NOPASSWD: ALL" > /etc/sudoers.d/open-sudo
RUN chmod 0440 /etc/sudoers.d/open-sudo
