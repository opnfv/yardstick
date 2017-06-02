#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a lmbench memory bandwidth benchmark in a host and
# output in json format the memory size in megabytes and
# memory bandwidth in megabytes per second

set -e

SIZE=$1
TEST_NAME=$2
WARMUP=$3

NODE_CPU_ARCH="$(uname -m)"

# write the result to stdout in json format
output_json()
{
    read DATA
    echo $DATA | awk '/ /{printf "{\"size(MB)\": %s, \"bandwidth(MBps)\": %s}", $1, $2}'
}

if [ "${NODE_CPU_ARCH}" == "aarch64" ]; then
    /usr/lib/lmbench/bin/bw_mem -W $WARMUP ${SIZE}k $TEST_NAME 2>&1 | output_json
else
    /usr/lib/lmbench/bin/x86_64-linux-gnu/bw_mem -W $WARMUP ${SIZE}k $TEST_NAME 2>&1 | output_json
fi
