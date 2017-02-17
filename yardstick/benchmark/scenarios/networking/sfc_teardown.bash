#!/bin/bash
##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

#set -e

#delete classifier
tacker sfc-classifier-delete red_http
tacker sfc-classifier-delete red_ssh

#delete service chain
tacker sfc-delete red
tacker sfc-delete blue

#delete VNFs
tacker vnf-delete testVNF1
tacker vnf-delete testVNF2

#delete VNF descriptor
tacker vnfd-delete test-vnfd1
tacker vnfd-delete test-vnfd2
