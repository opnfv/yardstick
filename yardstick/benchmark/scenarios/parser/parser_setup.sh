#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

git clone https://github.com/mbj4668/pyang.git /tmp/pyang
cd /tmp/pyang
python setup.py install
git clone https://gerrit.opnfv.org/gerrit/parser /tmp/parser

