#!/bin/sh

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

# Commandline arguments
PAYLOAD_OP=$1
shift
DURATION=$1
shift
EVENTS=("$@")
OUTPUT_FILE=/tmp/perfout.txt

# run perf test
run_perf()
{
    COMMA_SEP_E=$( IFS=$','; echo "${EVENTS[*]}" )

    if [[ $PAYLOAD_OP == dd* ]]
    then
        sudo perf stat -o $OUTPUT_FILE -e ${COMMA_SEP_E[@]} $PAYLOAD_OP &
        sleep $DURATION
        sudo killall -q -u root dd
    else
        sudo perf stat -o $OUTPUT_FILE -e ${COMMA_SEP_E[@]} $PAYLOAD_OP
    fi
}

# write the result to stdout in json format
output_json()
{
    EVENTS+=('time')

    last_pos=$(( ${#EVENTS[*]} - 1 ))
    last=${EVENTS[$last_pos]}

    echo -n {
    for EVENT in ${EVENTS[@]}
    do
        value=$(cat $OUTPUT_FILE | grep $EVENT | awk 'match($0,/[0-9]+|[0-9]+\.[0-9]*/, a) { print a[0]}')

        if [[ $EVENT != $last ]]
        then
            echo -n \"$EVENT\": $value,
        else
            echo -n \"$EVENT\": $value
        fi
    done
    echo }
}

# main entry
main()
{
    run_perf > /dev/null 2>&1
    sleep 1
    output_json
}

main
