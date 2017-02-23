#!/bin/bash
##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

#service iptables stop
python -m SimpleHTTPServer 80 > /dev/null 2>&1 &
touch index.html
echo "WORKED" >> index.html
