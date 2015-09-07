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
OUTPUT_FILE=/tmp/cyclictest-out.log

# run cyclictest test
run_cyclictest()
{
    cyclictest $OPTIONS > $OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
    min=$(awk '/# Min Latencies:/{print $4}' $OUTPUT_FILE)
    avg=$(awk '/# Avg Latencies:/{print $4}' $OUTPUT_FILE)
    max=$(awk '/# Max Latencies:/{print $4}' $OUTPUT_FILE)
    echo -e "{ \
        \"min\":\"$min\", \
        \"avg\":\"$avg\", \
        \"max\":\"$max\" \
    }"
}

# main entry
main()
{
    # run the test
    run_cyclictest

    # output result
    output_json
}

main

