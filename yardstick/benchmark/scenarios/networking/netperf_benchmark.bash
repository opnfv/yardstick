#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

# Commandline arguments
OPTIONS="$@"
OUTPUT_FILE=/tmp/netperf-out.log

# run netperf test
run_netperf()
{
    netperf $OPTIONS > $OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
    mean=$(awk '/\/s/{print $3}' $OUTPUT_FILE)
    troughput=$(awk '/\/s/{print $1}' $OUTPUT_FILE)
    unit=$(awk '/\/s/{print $2}' $OUTPUT_FILE)
    echo -e "{ \
        \"mean_latency\":\"$mean\", \
        \"troughput\":\"$troughput\", \
        \"troughput_unit\":\"$unit\" \
    }"
}

# main entry
main()
{
    # run the test
    run_netperf

    # output result
    output_json
}

main