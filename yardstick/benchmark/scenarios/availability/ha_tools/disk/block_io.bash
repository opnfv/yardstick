#!/bin/bash

##############################################################################
# (c) OPNFV, Yin Kanglin and others.
# 14_ykl@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# make a disk IO jam

sudo dd if=/dev/zero of=/test.dbf bs=8k count=30000000 &
