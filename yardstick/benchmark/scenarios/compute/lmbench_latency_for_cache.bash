#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a lmbench cache latency benchmark in a host and
# outputs in json format the array sizes in megabytes and
# load latency over all points in that array in nanosecods

set -e

REPETITON=$1
WARMUP=$2

NODE_CPU_ARCH="$(uname -m)"

# write the result to stdout in json format
output_json()
{
    read DATA
    echo $DATA | awk '{printf "{\"L1cache\": %s}", $5}'
}


if [ "${NODE_CPU_ARCH}" == "aarch64" ]; then
    /usr/lib/lmbench/bin/cache -W $WARMUP -N $REPETITON  2>&1 | output_json
else
    /usr/lib/lmbench/bin/x86_64-linux-gnu/cache -W $WARMUP -N $REPETITON  2>&1 | output_json
fi
