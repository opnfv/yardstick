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
OUTPUT_FILE="yardstick-fio.log"

# setup data file for fio
setup()
{
    if [ ! -f $FIO_FILENAME ]; then
        dd if=/dev/zero of=$FIO_FILENAME bs=1M count=1024 oflag=direct > /dev/null 2>&1
    fi
}

# run fio test
run_test()
{
    fio $OPTIONS --output=$OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
    read_bw=$(grep "READ.*aggrb"  $OUTPUT_FILE | awk -F [=\ ,] '{printf $9}')
    write_bw=$(grep "WRITE.*aggrb" $OUTPUT_FILE | awk -F [=\ ,] '{printf $8}')
    eval $(grep -e '\ lat.*stdev' -e "read.*iops" -e "write.*iops" -e "trim.*iops" $OUTPUT_FILE | sed 'N;s/\n/ /g' | grep read | awk -F [=\ ,\(\)] '{printf("read_iops=%s; read_lat_unit=%s; read_lat=%s", $12, $24, $33)}')
    eval $(grep -e '\ lat.*stdev' -e "read.*iops" -e "write.*iops" -e "trim.*iops" $OUTPUT_FILE | sed 'N;s/\n/ /g' | grep write | awk -F [=\ ,\(\)] '{printf("write_iops=%s; write_lat_unit=%s; write_lat=%s", $11, $23, $32)}')

    read_bw=${read_bw:-N/A}
    write_bw=${write_bw:-N/A}
    read_iops=${read_iops:-N/A}
    write_iops=${write_iops:-N/A}
    if [ "x$read_lat" = "x" ]; then
        read_lat="N/A"
    else
        read_lat=$read_lat$read_lat_unit
    fi
    if [ "x$write_lat" = "x" ]; then
        write_lat="N/A"
    else
        write_lat=$write_lat$write_lat_unit
    fi

    echo -e "{ \
        \"read_bw\":\"$read_bw\", \
        \"write_bw\":\"$write_bw\", \
        \"read_iops\":\"$read_iops\", \
        \"write_iops\":\"$write_iops\", \
        \"read_lat\":\"$read_lat\", \
        \"write_lat\":\"$write_lat\" \
    }"
}

# main entry
main()
{
    # setup the test
    setup

    # run the test
    run_test >/dev/null

    # output result
    output_json
}

main

