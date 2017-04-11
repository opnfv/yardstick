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
DST_IP=$1         # destination IP address
NUM_PORTS=$2      # number of source ports
PKT_SIZE=$3       # packet size
DURATION=$4       # test duration (seconds)
TRXQUEUE=$5       # number of RX/TX queues to use
PPS=$6            # packets per second to send

# Configuration
UDP_SRC_MIN=1000                               # UDP source port min
UDP_SRC_MAX=$(( UDP_SRC_MIN + NUM_PORTS - 1 )) # UDP source port max
UDP_DST_MIN=1000                               # UDP destination port min
UDP_DST_MAX=$(( UDP_DST_MIN + NUM_PORTS ))     # UDP destination port max

# helper function to send commands to pktgen
pgset()
{
    local result

    echo $1 > $PGDEV

    result=$(cat $PGDEV | fgrep "Result: OK:")
    if [ "$result" = "" ]; then
        cat $PGDEV | fgrep "Result:" >/dev/stderr
        exit 1
    fi
}

# remove all devices from thread
pgclean()
{
    COUNTER=0
    while [ ${COUNTER} -lt ${TRXQUEUE} ]; do
        #
        # Thread commands
        #

        PGDEV=/proc/net/pktgen/kpktgend_${COUNTER}

        # Remove all devices from this thread
        pgset "rem_device_all"
        let COUNTER=COUNTER+1
    done
}

# configure pktgen (see pktgen doc for details)
pgconfig()
{
    pps=$(( PPS / TRXQUEUE ))
    COUNTER=0
    while [ ${COUNTER} -lt ${TRXQUEUE} ]; do
        #
        # Thread commands
        #

        PGDEV=/proc/net/pktgen/kpktgend_${COUNTER}

        # Add device to thread
        pgset "add_device $DEV@${COUNTER}"

        #
        # Device commands
        #

        PGDEV=/proc/net/pktgen/$DEV@${COUNTER}

        # 0 means continious sends untill explicitly stopped
        pgset "count 0"

        # set pps count to test with an explicit number. if 0 will try with bandwidth
        if [ ${pps} -gt 0 ]
        then
            pgset "ratep ${pps}"
        fi

        pgset "clone_skb 10"

        # use different queue per thread
        pgset "queue_map_min ${COUNTER}"
        pgset "queue_map_max ${COUNTER}"

        # packet size, NIC adds 4 bytes CRC
        pgset "pkt_size $PKT_SIZE"

        # random address within the min-max range
        pgset "flag UDPDST_RND"
        pgset "flag UDPSRC_RND"
        pgset "flag IPDST_RND"

        # destination IP
        pgset "dst_min $DST_IP"
        pgset "dst_max $DST_IP"

        # destination MAC address
        pgset "dst_mac $MAC"

        # source UDP port range
        pgset "udp_src_min $UDP_SRC_MIN"
        pgset "udp_src_max $UDP_SRC_MAX"

        # destination UDP port range
        pgset "udp_dst_min $UDP_DST_MIN"
        pgset "udp_dst_max $UDP_DST_MAX"

        let COUNTER=COUNTER+1

    done
}

# run pktgen
pgrun()
{
    # Time to run, result can be viewed in /proc/net/pktgen/$DEV
    PGDEV=/proc/net/pktgen/pgctrl
    # Will hang, Ctrl-C or SIGINT to stop
    pgset "start" start

    COUNTER=0
    while [ ${COUNTER} -lt ${TRXQUEUE} ]; do
        taskset -c ${COUNTER} kpktgend_${COUNTER}
        let COUNTER=COUNTER+1
    done
}

# run pktgen for ${DURATION} seconds
run_test()
{
    pgrun &
    pid=$!

    sleep $DURATION

    kill -INT $pid

    wait; sleep 1
}

# write the result to stdout in json format
output_json()
{
    sent=0
    result_pps=0
    errors=0
    PGDEV=/proc/net/pktgen/$DEV@
    COUNTER=0
    while [ ${COUNTER} -lt ${TRXQUEUE} ]; do
        sent=$(($sent + $(awk '/^Result:/{print $5}' <$PGDEV${COUNTER})))
        result_pps=$(($result_pps + $(awk 'match($0,/'\([0-9]+\)pps'/, a) {print a[1]}' <$PGDEV${COUNTER})))
        errors=$(($errors + $(awk '/errors:/{print $5}' <$PGDEV${COUNTER})))
        let COUNTER=COUNTER+1
    done

    flows=$(( NUM_PORTS * (NUM_PORTS + 1) ))

    echo '{ "packets_sent"':${sent} , '"packets_per_second"':${result_pps}, '"flows"':${flows}, '"errors"':${errors} '}'
}

# main entry
main()
{
    modprobe pktgen
    pgclean

    ping -c 3 $DST_IP >/dev/null

    # destination MAC address
    MAC=`arp -n | grep -w $DST_IP | awk '{print $3}'`

    # outgoing interface
    DEV=`arp -n | grep -w $DST_IP | awk '{print $5}'`

    # setup the test
    pgconfig

    # run the test
    run_test

    PGDEV=/proc/net/pktgen/$DEV@

    # check result
    COUNTER=0
    while [  ${COUNTER} -lt ${TRXQUEUE} ]; do
        result=$(cat $PGDEV${COUNTER} | fgrep "Result: OK:")
        if [ "$result" = "" ]; then
            cat $PGDEV${COUNTER} | fgrep Result: >/dev/stderr
            exit 1
        fi
        let COUNTER=COUNTER+1
    done

    # output result
    output_json
}

main

