#!/bin/bash
##############################################################################
# Copyright (c) 2017 ZTE corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
!/bin/sh

set -e

# Commandline arguments
SRC_IP=$1         # source IP address of sender in VM A
DST_IP=$2         # destination IP address of receiver in VM A
FWD_REV_MAC=$3    # MAC address of forwarding receiver in VM B
FWD_SEND_MAC=$4   # MAC address of forwarding sender in VM B
RATE=$5           # packet rate in percentage
PKT_SIZE=$6       # packet size


load_modules()
{
    if lsmod | grep "uio" &> /dev/null ; then
    echo "uio module is loaded"
    else
    modprobe uio
    fi

    if lsmod | grep "igb_uio" &> /dev/null ; then
    echo "igb_uio module is loaded"
    else
    insmod /dpdk/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    fi

    if lsmod | grep "rte_kni" &> /dev/null ; then
    echo "rte_kni module is loaded"
    else
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
    /dpdk/tools/dpdk-devbind.py --bind=igb_uio $interfaces

}

create_pktgen_config_lua()
{
    touch /home/ubuntu/pktgen_latency.lua
    lua_file="/home/ubuntu/pktgen_latency.lua"
    chmod 777 $lua_file
    echo $lua_file

    cat << EOF > "/home/ubuntu/pktgen_latency.lua"
package.path = package.path ..";?.lua;test/?.lua;app/?.lua;"

 -- require "Pktgen";
function pktgen_config()

  pktgen.screen("off");

  pktgen.set_ipaddr("0", "dst", "$DST_IP");
  pktgen.set_ipaddr("0", "src", "$SRC_IP/24");
  pktgen.set_mac("0", "$FWD_REV_MAC");
  pktgen.set_ipaddr("1", "dst", "$SRC_IP");
  pktgen.set_ipaddr("1", "src", "$DST_IP/24");
  pktgen.set_mac("1", "$FWD_SEND_MAC");
  pktgen.set(0, "rate", $RATE);
  pktgen.set(0, "size", $PKT_SIZE);
  pktgen.set_proto("all", "udp");
  pktgen.latency("all","enable");
  pktgen.latency("all","on");

  pktgen.start(0);
  end

pktgen_config()
EOF
}


create_expect_file()
{
    touch /home/ubuntu/pktgen.exp
    expect_file="/home/ubuntu/pktgen.exp"
    chmod 777 $expect_file
    echo $expect_file

    cat << 'EOF' > "/home/ubuntu/pktgen.exp"
#!/usr/bin/expect

set blacklist  [lindex $argv 0]
set log [lindex $argv 1]
set result {}
set timeout 15
spawn ./app/app/x86_64-native-linuxapp-gcc/pktgen -c 0x07 -n 4 -b $blacklist -- -P -m "1.0, 2.1" -f /home/ubuntu/pktgen_latency.lua
expect "Pktgen>"
send "\n"
expect "Pktgen>"
send "screen on\n"
expect "Pktgen>"
set count 10
while { $count } {
    send "page latency\n"
    expect {
        timeout { send "\n" }
        -regexp {..*} {
            set result "${result}$expect_out(0,string)"
            set timeout 1
            exp_continue
         }
        "Pktgen>"
    }
    set count [expr $count-1]
}
send "stop 0\n"
expect "Pktgen>"
send "quit\n"
expect "#"

set file [ open $log w ]
puts $file $result
EOF

}

run_pktgen()
{
    blacklist=$(lspci |grep Eth |awk '{print $1}'|head -1)
    cd /pktgen-dpdk
    touch /home/ubuntu/result.log
    result_log="/home/ubuntu/result.log"
    sudo expect /home/ubuntu/pktgen.exp $blacklist $result_log
}

main()
{
    load_modules
    change_permissions
    create_pktgen_config_lua
    create_expect_file
    add_interface_to_dpdk
    run_pktgen
}

main

