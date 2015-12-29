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
yangfile=$1
base_dir=$(dirname $yangfile)
shift
toscafile=$1
OUTPUT_FILE=/tmp/parser-out.log

# run parser test
run_parser()
{
    cd /tmp/parser/yang2tosca
    python tosca_translator.py  --filename $yangfile> $OUTPUT_FILE
}

# write the result to stdout in json format
check_result()
{

    if (diff -q $toscafile ${yangfile%'.yaml'}"_tosca.yaml" >> $OUTPUT_FILE);
        then
        exit 0
    else
        exit 1
    fi

}

# main entry
main()
{
    # run the test
    run_parser

    # output result
    check_result
}

main
