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
OUTPUT_FILE=/tmp/unixbench-out.log

# run netperf test
run_unixbench()
{
    cd /opt/tempT/UnixBench/
    ./Run $OPTIONS > $OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
    signle_score=$(awk '/Score/{print $7}' $OUTPUT_FILE | head -1 )
    parallel_score=$(awk '/Score/{print $7}' $OUTPUT_FILE | tail -1 )
    echo -e "{  \
        \"signle_score\":\"$signle_score\", \
        \"parallel_score\":\"$parallel_score\" \
    }"
}

# main entry
main()
{
    # run the test
    run_unixbench

    # output result
    output_json
}

main
