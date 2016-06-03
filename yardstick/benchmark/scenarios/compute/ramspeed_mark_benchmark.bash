#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a ramspeed memory bandwidth benchmark in a host and
# output in json format the memory bandwidth in megabytes per second

set -e

TYPE_ID=$1
LOAD=$2
BLOCK_SIZE=$3
OUTPUT_FILE=/tmp/ramspeed-out.log

run_ramspeed()
{
    cd /opt/tempT/RAMspeed/ramspeed-2.6.0/
    ./ramspeed -b $TYPE_ID -g $LOAD -m $BLOCK_SIZE > $OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
   SCORE=$(awk '/  /{printf "{\"Test_type\": \"%s %s %s\", \"Block_size(kb)\": %s, \"Bandwidth(MBps)\": %s},", $1, $2, $3, $4, $7}' $OUTPUT_FILE)
   echo -e "{ \
       \"Result\":[${SCORE%?}] \
   }"
}

main()
{
    # run the test
    run_ramspeed

    #output result
    output_json
}

main
