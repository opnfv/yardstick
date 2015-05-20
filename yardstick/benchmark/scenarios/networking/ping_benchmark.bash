#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a single ping command towards a destination and outputs the round trip
# time in milliseconds on stdout. The count (-c) option is deliberately not
# supported since it is supposed to be handled by the runner.

set -e

destination=$1
shift
options="$@"

ping -c 1 $options $destination | grep ttl | awk -F [=\ ] '{printf $10}'
