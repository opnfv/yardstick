#!/bin/sh

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

# Commandline arguments
FIO_FILENAME=$1
shift
OPTIONS="$@"

# setup data file for fio
setup()
{
    if [ ! -f $FIO_FILENAME ]; then
        dd if=/dev/zero of=$FIO_FILENAME bs=1M count=1024 oflag=direct > /dev/null 2>&1
    fi
}

# run fio test and write json format result to stdout
run_test()
{
    fio $OPTIONS
}

# main entry
main()
{
    # setup the test
    setup

    # run the test
    run_test
}

main

