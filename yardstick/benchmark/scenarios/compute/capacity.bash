#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Measure hardware capacity and scale of a host

set -e

# run capacity test
run_capacity()
{
    # Number of CPUs
    CPU=$(grep 'physical id' /proc/cpuinfo | sort -u | wc -l)
    # Number of physical cores in a single CPU
    CORE=$(grep 'core id' /proc/cpuinfo | sort -u | wc -l)
    # Total physical core number
    CORES=$[$CPU * $CORE]
    # Number of logical cores
    THREAD=$(grep 'processor' /proc/cpuinfo | sort -u | wc -l)
    # Total memory size
    MEMORY=$(grep 'MemTotal' /proc/meminfo | sort -u)
    ME=$(echo $MEMORY | awk '/ /{printf "%s %s", $2, $3}')
    # Cache size per CPU
    CACHE=$(grep 'cache size' /proc/cpuinfo | sort -u)
    CA=$(echo $CACHE | awk '/ /{printf "%s", $4}')
    CACHES=$[$CA * $CPU]
}

# write the result to stdout in json format
output_json()
{
    echo -e "{ \
        \"Cpu_number\":\"$CPU\", \
        \"Core_number\":\"$CORES\", \
        \"Thread_number\":\"$THREAD\", \
        \"Memory_size\": \"$ME\", \
        \"Cache_size\": \"$CACHES KB\" \
    }"
}

main()
{
    run_capacity

    output_json
}

main
