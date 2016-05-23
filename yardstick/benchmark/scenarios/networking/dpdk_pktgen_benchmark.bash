#!/bin/sh

set -e

# Commandline arguments
DST_IP=$1         # destination IP address
NUM_PORTS=$2      # number of source ports
PKT_SIZE=$3       # packet size
DURATION=$4       # test duration (seconds)
SRC_IP=$5         # destination IP address

# Configuration
#UDP_SRC_MIN=1000                               # UDP source port min
#UDP_SRC_MAX=$(( UDP_SRC_MIN + NUM_PORTS - 1 )) # UDP source port max
#UDP_DST_MIN=1000                               # UDP destination port min
#UDP_DST_MAX=$(( UDP_DST_MIN + NUM_PORTS ))     # UDP destination port max

echo $DST_IP $SRC_IP $NUM_PORTS $PKT_SIZE $DURATION $MAC $DEV>> ~/res.txt
