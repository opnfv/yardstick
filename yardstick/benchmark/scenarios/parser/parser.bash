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
OUTPUT_FILE=/tmp/parser-out.log

# run parser test
run_parser()
{
    cd /opt/temp/parser/yang2tosca
    python tosca_translator.py  --filename ~/yang.yaml > $OUTPUT_FILE
    cd ~
}

# write the result to stdout in json format
check_result()
{

    if (diff -q tosca.yaml yang_tosca.yaml >> $OUTPUT_FILE);
        then
        echo -e "{  \
            \"result\":\"success\" \
        }"
    else
        echo -e "{  \
            \"result\":\"failed\" \
        }"
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
