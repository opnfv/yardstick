#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Measure network capacity and scale of a host

set -e
OUTPUT_FILE=/tmp/netperf-out.log

# run capacity test
run_capacity()
{
    netstat -s > $OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
    CONNECTIONS=$(awk '/active/{print $1}' $OUTPUT_FILE)
    FRAMES=$(awk '/total\ packets\ received/{print $1}' $OUTPUT_FILE)
    echo -e "{ \
        \"Number of connections\":\"$CONNECTIONS\", \
        \"Number of frames received\": \"$FRAMES\" \
    }"
}

main()
{
    run_capacity

    output_json
}

main
