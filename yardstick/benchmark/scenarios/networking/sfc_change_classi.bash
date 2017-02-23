#!/bin/bash
##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
tacker sfc-classifier-delete red_http
tacker sfc-classifier-delete red_ssh

tacker sfc-classifier-create --name blue_http --chain blue --match source_port=0,dest_port=80,protocol=6
tacker sfc-classifier-create --name blue_ssh  --chain blue --match source_port=0,dest_port=22,protocol=6

tacker sfc-classifier-list
