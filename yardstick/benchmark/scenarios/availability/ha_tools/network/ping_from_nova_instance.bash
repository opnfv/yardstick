#!/bin/bash

##############################################################################
# Copyright (c) 2018 Intracom Telecom and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# this script checks the communication between nova instances
# or between a nova instance and an external domain via ping
# Usage:
#   ssh <user>@<floating_ip> ping <destination_ip>
# parameter user - nova instance user
# parameter floating_ip - nova instance floating ip
# parameter destination_ip - nova instance destination ip or external domain

ssh $1@$2 ping $3 -c 1
