#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# compute capacity and scale of a host

set -e

# run capacity test
run_capacity()
{
    #parameter used for HT(Hyper-Thread) check
    HT_Para=2
    # Number of CPUs
    CPU=$(grep 'physical id' /proc/cpuinfo | sort -u | wc -l)
    # Number of physical cores in a single CPU
    CORE=$(grep 'core id' /proc/cpuinfo | sort -u | wc -l)
    # Total physical core number
    CORES=$[$CPU * $CORE]
    # Number of logical cores
    THREAD=$(grep 'processor' /proc/cpuinfo | sort -u | wc -l)
    # Total memory size
    MEMORY=$(grep 'MemTotal' /proc/meminfo | sort -u | awk '{print $2}')

    # Cache size per CPU
    CACHE=$(grep 'cache size' /proc/cpuinfo | sort -u | awk '{print $4}')
    CACHES=$[$CACHE * $CPU]
    HT_Value=$[$HT_Para * $CORES]
    if [ $HT_Value -eq $THREAD ]; then
        HT_OPEN=1
    else
        HT_OPEN=0
    fi
}

# write the result to stdout in json format
output_json()
{
    echo -e "{ \
        \"Cpu_number\":\"$CPU\", \
        \"Core_number\":\"$CORES\", \
        \"Thread_number\":\"$THREAD\", \
        \"Memory_size\": \"$MEMORY\", \
        \"Cache_size\": \"$CACHES\", \
        \"HT_Open\": \"$HT_OPEN\" \
    }"
}

main()
{
    run_capacity

    output_json
}

main
