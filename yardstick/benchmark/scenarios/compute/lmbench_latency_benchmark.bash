#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a lmbench read memory latency benchmark in a host and
# outputs in json format the array sizes in megabytes and
# load latency over all points in that array in nanosecods

set -e

SIZE=$1
shift
STRIDE=$1

NODE_CPU_ARCH="$(uname -m)"

# write the result to stdout in json format
output_json()
{
    iter=0
    echo [
    while read DATA
    do
        if [ $iter -gt 1 ] && [ -n "$DATA" ]; then
            echo ,
        fi

        echo -n $DATA | awk '/ /{printf "{\"size\": %s, \"latency\": %s}", $1, $2}'

        iter=$((iter+1))
    done
    echo ]
}

if [ "${NODE_CPU_ARCH}" == "aarch64" ]; then
    /usr/lib/lmbench/bin/lat_mem_rd $SIZE $STRIDE 2>&1 | output_json
else
    /usr/lib/lmbench/bin/x86_64-linux-gnu/lat_mem_rd $SIZE $STRIDE 2>&1 | output_json
fi
