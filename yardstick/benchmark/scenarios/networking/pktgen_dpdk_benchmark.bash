##############################################################################
# Copyright (c) 2017 Nokia and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
#!/bin/sh

set -e

# Commandline arguments
SRC_IP=$1         # source IP address
DST_IP=$2         # destination IP address
DST_MAC=$3        # destination MAC address
NUM_PORTS=$4      # number of source ports
PKT_SIZE=$5       # packet size
DURATION=$6       # test duration (seconds)
RATE=$7           # packet rate in percentage for 10G NIC

MAX_RATE=100

# Configuration
UDP_SRC_MIN=1000                               # UDP source port min
UDP_SRC_MAX=$(( UDP_SRC_MIN + NUM_PORTS - 1 )) # UDP source port max
UDP_DST_MIN=1000                               # UDP destination port min
UDP_DST_MAX=$(( UDP_DST_MIN + NUM_PORTS ))     # UDP destination port max

load_modules()
{
    if ! lsmod | grep "uio" &> /dev/null; then
        modprobe uio
    fi

    if ! lsmod | grep "igb_uio" &> /dev/null; then
        insmod /dpdk/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    fi

    if ! lsmod | grep "rte_kni" &> /dev/null; then
        insmod /dpdk/x86_64-native-linuxapp-gcc/kmod/rte_kni.ko
    fi
}

change_permissions()
{
    chmod 777 /sys/bus/pci/drivers/virtio-pci/*
    chmod 777 /sys/bus/pci/drivers/igb_uio/*
}

add_interface_to_dpdk(){
    interfaces=$(lspci |grep Eth |tail -n +2 |awk '{print $1}')
    /dpdk/usertools/dpdk-devbind.py --bind=igb_uio $interfaces &> /dev/null
}

create_pktgen_config_lua()
{
    lua_file="/home/ubuntu/pktgen_tput.lua"
    touch $lua_file
    chmod 777 $lua_file

    cat << EOF > "/home/ubuntu/pktgen_tput.lua"
package.path = package.path ..";?.lua;test/?.lua;app/?.lua;"

 -- require "Pktgen";
function pktgen_config()

  pktgen.screen("off");

  pktgen.set_ipaddr("0", "src", "$SRC_IP/24");
  pktgen.set_ipaddr("0", "dst", "$DST_IP");
  pktgen.set_mac("0", "$DST_MAC");
  pktgen.set("all", "sport", $UDP_SRC_MIN);
  pktgen.set("all", "dport", $UDP_DST_MIN);
  pktgen.set("all", "size", $PKT_SIZE);
  pktgen.set("all", "rate", $RATE);
  pktgen.set_type("all", "ipv4");
  pktgen.set_proto("all", "udp");

  pktgen.src_ip("0", "start", "$SRC_IP");
  pktgen.src_ip("0", "inc", "0.0.0.0");
  pktgen.src_ip("0", "min", "$SRC_IP");
  pktgen.src_ip("0", "max", "$SRC_IP");
  pktgen.dst_ip("0", "start", "$DST_IP");
  pktgen.dst_ip("0", "inc", "0.0.0.0");
  pktgen.dst_ip("0", "min", "$DST_IP");
  pktgen.dst_ip("0", "max", "$DST_IP");

  pktgen.dst_mac("0", "start", "$DST_MAC");

  pktgen.src_port("all", "start", $UDP_SRC_MIN);
  pktgen.src_port("all", "inc", 1);
  pktgen.src_port("all", "min", $UDP_SRC_MIN);
  pktgen.src_port("all", "max", $UDP_SRC_MAX);
  pktgen.dst_port("all", "start", $UDP_DST_MIN);
  pktgen.dst_port("all", "inc", 1);
  pktgen.dst_port("all", "min", $UDP_DST_MIN);
  pktgen.dst_port("all", "max", $UDP_DST_MAX);

  pktgen.pkt_size("all", "start", $PKT_SIZE);
  pktgen.pkt_size("all", "inc",0);
  pktgen.pkt_size("all", "min", $PKT_SIZE);
  pktgen.pkt_size("all", "max", $PKT_SIZE);
  pktgen.ip_proto("all", "udp");
  pktgen.set_range("all", "on");

  pktgen.start("all");
  pktgen.sleep($DURATION)
  pktgen.stop("all");
  pktgen.sleep(1)

  prints("opackets", pktgen.portStats("all", "port")[0].opackets);
  prints("oerrors", pktgen.portStats("all", "port")[0].oerrors);

  end

pktgen_config()
EOF
}


create_expect_file()
{
    expect_file="/home/ubuntu/pktgen_tput.exp"
    touch $expect_file
    chmod 777 $expect_file

    cat << 'EOF' > "/home/ubuntu/pktgen_tput.exp"
#!/usr/bin/expect

set blacklist  [lindex $argv 0]
spawn ./app/app/x86_64-native-linuxapp-gcc/pktgen -c 0x0f -n 4 -b $blacklist -- -P -m "{2-3}.0" -f /home/ubuntu/pktgen_tput.lua
expect "Pktgen"
send "on\n"
expect "Pktgen"
send "page main\n"
expect "Pktgen"
sleep 1
send "quit\n"
expect "#"

EOF

}

run_pktgen()
{
    blacklist=$(lspci |grep Eth |awk '{print $1}'|head -1)
    cd /pktgen-dpdk
    result_log="/home/ubuntu/result.log"
    touch $result_log
    sudo expect /home/ubuntu/pktgen_tput.exp $blacklist > $result_log 2>&1
}

# write the result to stdout in json format
output_json()
{
    sent=0
    result_pps=0
    errors=0

    sent=$(cat ~/result.log -vT | grep "Tx Pkts" | tail -1 | awk '{match($0,/\[18;20H +[0-9]+/)} {print substr($0,RSTART,RLENGTH)}' | awk '{if ($2 != 0) print $2}')
    result_pps=$(( sent / DURATION ))
    errors=$(cat ~/result.log -vT |grep "Errors Rx/Tx" | tail -1 | awk '{match($0,/\[16;20H +[0-9]+\/+[0-9]+/)} {print substr($0,RSTART,RLENGTH)}' | cut -d '/' -f2)

    flows=$(( NUM_PORTS * (NUM_PORTS + 1) ))

    echo '{ "packets_sent"':${sent} , '"packets_per_second"':${result_pps}, '"flows"':${flows}, '"errors"':${errors} '}'
}

main()
{
    if ip a | grep eth2 >/dev/null 2>&1; then
        ip link set eth2 down
    fi

    if ip a | grep eth1 >/dev/null 2>&1; then
        ip link set eth1 down
        load_modules
        change_permissions
        add_interface_to_dpdk
    fi

    if [ $RATE -gt $MAX_RATE ]; then
        RATE=$MAX_RATE
    fi

    create_pktgen_config_lua
    create_expect_file

    run_pktgen

    output_json
}

main
