#!/bin/sh

set -e

# Commandline arguments
DST_IP=$1         # destination IP address
shift
NUM_PORTS=$1      # number of source ports
shift
PKT_SIZE=$1       # packet size

# Configuration
UDP_SRC_MIN=1000                               # UDP source port min
UDP_SRC_MAX=$(( UDP_SRC_MIN + NUM_PORTS - 1 )) # UDP source port max
UDP_DST_MIN=1000                               # UDP destination port min
UDP_DST_MAX=$(( UDP_DST_MIN + NUM_PORTS ))     # UDP destination port max
DURATION=20                                    # test duration (seconds)

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

# configure pktgen (see pktgen doc for details)
pgconfig()
{
    #
    # Thread commands
    #

    PGDEV=/proc/net/pktgen/kpktgend_0

    # Remove all devices from this thread
    pgset "rem_device_all"

    # Add device to thread
    pgset "add_device $DEV"

    #
    # Device commands
    #

    PGDEV=/proc/net/pktgen/$DEV

    # 0 means continious sends untill explicitly stopped
    pgset "count 0"

    # use single SKB for all transmits
    pgset "clone_skb 0"

    # packet size, NIC adds 4 bytes CRC
    pgset "pkt_size $PKT_SIZE"

    # random address within the min-max range
    pgset "flag IPDST_RND UDPSRC_RND UDPDST_RND"

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
}

# run pktgen
pgrun()
{
    # Time to run, result can be vieved in /proc/net/pktgen/$DEV
    PGDEV=/proc/net/pktgen/pgctrl
    # Will hang, Ctrl-C or SIGINT to stop
    pgset "start" start
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
    sent=$(awk '/^Result:/{print $5}' <$PGDEV)
    pps=$(awk 'match($0,/'\([0-9]+\)pps'/, a) {print a[1]}' <$PGDEV)
    errors=$(awk '/errors:/{print $5}' <$PGDEV)

    flows=$(( NUM_PORTS * (NUM_PORTS + 1) ))

    echo { '"packets_sent"':$sent , '"packets_per_second"':$pps, '"flows"':$flows, '"errors"':$errors }
}

# main entry
main()
{
    modprobe pktgen

    ping -c 3 $DST_IP >/dev/null

    # destination MAC address
    MAC=`arp -n | grep -w $DST_IP | awk '{print $3}'`

    # outgoing interface
    DEV=`arp -n | grep -w $DST_IP | awk '{print $5}'`

    # setup the test
    pgconfig

    # run the test
    run_test >/dev/null

    PGDEV=/proc/net/pktgen/$DEV

    # check result
    result=$(cat $PGDEV | fgrep "Result: OK:")
    if [ "$result" = "" ]; then
         cat $PGDEV | fgrep Result: >/dev/stderr
         exit 1
    fi

    # output result
    output_json
}

main

