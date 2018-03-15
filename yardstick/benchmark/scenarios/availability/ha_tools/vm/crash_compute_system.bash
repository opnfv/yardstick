#!/bin/bash

##############################################################################
# Copyright (c) 2018 CMRI and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# check the status of a service

set -e

ssh -o ServerAliveInterval=2 -i /etc/yardstick/ssh/id_rsa -F /etc/yardstick/ssh/config root@host2
echo 1 > /proc/sys/kernel/sysrq
echo "crash $1 success!"
echo c > /proc/sysrq-trigger

