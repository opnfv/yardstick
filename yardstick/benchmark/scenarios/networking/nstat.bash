#!/bin/bash

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Monitor network metrics provided by the kernel in a host and calculate
# IP datagram error rate, ICMP message error rate, TCP segment error rate and
# UDP datagram error rate.

set -e
DURATION=$1
OUTPUT_FILE=/tmp/nstat-out.log

run_nstat()
{
    sleep $DURATION
    nstat -z > $OUTPUT_FILE
}

output_json()
{
    IpInReceives=$(awk '/IpInReceives/{print $2}' $OUTPUT_FILE)
    IpInHdrErrors=$(awk '/IpInHdrErrors/{print $2}' $OUTPUT_FILE)
    IpInAddrErrors=$(awk '/IpInAddrErrors/{print $2}' $OUTPUT_FILE)
    IcmpInMsgs=$(awk '/IcmpInMsgs/{print $2}' $OUTPUT_FILE)
    IcmpInErrors=$(awk '/IcmpInErrors/{print $2}' $OUTPUT_FILE)
    TcpInSegs=$(awk '/TcpInSegs/{print $2}' $OUTPUT_FILE)
    TcpInErrs=$(awk '/TcpInErrs/{print $2}' $OUTPUT_FILE)
    UdpInDatagrams=$(awk '/UdpInDatagrams/{print $2}' $OUTPUT_FILE)
    UdpInErrors=$(awk '/UdpInErrors/{print $2}' $OUTPUT_FILE)
    IpErrors=$[$IpInHdrErrors + $IpInAddrErrors]
    IP_datagram_error_rate=$(echo "scale=3; $IpErrors/$IpInReceives" | bc)
    Icmp_message_error_rate=$(echo "scale=3; $IcmpInErrors/$IcmpInMsgs" | bc)
    Tcp_segment_error_rate=$(echo "scale=3; $TcpInErrs/$TcpInSegs" | bc)
    Udp_datagram_error_rate=$(echo "scale=3; $UdpInErrors/$UdpInDatagrams" | bc)
    echo -e "{ \
        \"IpInReceives\":\"$IpInReceives\", \
        \"IP_datagram_error_rate\":\"$IP_datagram_error_rate\", \
        \"IcmpInMsgs\":\"$IcmpInMsgs\", \
        \"Icmp_message_error_rate\":\"$Icmp_message_error_rate\", \
        \"TcpInSegs\":\"$TcpInSegs\", \
        \"Tcp_segment_error_rate\":\"$Tcp_segment_error_rate\", \
        \"UdpInDatagrams\":\"$UdpInDatagrams\", \
        \"Udp_datagram_error_rate\":\"$Udp_datagram_error_rate\" \
    }"
}

main()
{
    # run the test
    run_nstat
    # output result
    output_json
}

main
