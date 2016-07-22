#!/bin/sh

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
    /dpdk/tools/dpdk_nic_bind.py --bind=igb_uio 00:07.0 00:08.0
}

create_pktgen_config_lua()
{
    touch /home/pktgen_config.lua
    lua_file="/home/pktgen_config.lua"
    chmod 777 $lua_file
    echo $lua_file

    cat << EOF > "/home/pktgen_config.lua"
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
  pktgen.process("all", "on");
  -- latency enable lua api is not supported yet 2016/7/20
  -- pktgen.latency("all","enable")
  -- pktgen.latency("all","on")

  end

pktgen_config()
EOF
}


create_expect_file()
{
    touch /home/pktgen.exp
    expect_file="/home/pktgen.exp"
    chmod 777 $expect_file
    echo $expect_file

    cat << 'EOF' > "/home/pktgen.exp"
#!/usr/bin/expect

set config_lua [lindex $argv 0]
set log [lindex $argv 1]
set result {}
set timeout 15
spawn ./app/app/x86_64-native-linuxapp-gcc/pktgen -c 0x07 -n 4 -b 00:03.0 -- -P -m "1.0, 2.1"
send "\n"
expect "Pktgen>"
set timeout 2
send "script $config_lua\n"
expect "Pktgen>"
send "latency 0-1 enable\n"
expect "Pktgen>"
send "latency 0-1 on\n"
expect "Pktgen>"
send "start 0\n"
expect "Pktgen>"
send "screen on\n"
expect "Pktgen>"
set count 3
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
    cd /pktgen-dpdk
    touch /home/result.log
    latency_measure="/home/latency_measure.log"
    expect /home/pktgen.exp "/home/pktgen_config.lua" $latency_measure
    avg_latency=$(cat $latency_measure -vT |awk '{match($0,/\[8;40H +[0-9]+/)}{print substr($0,RSTART,RLENGTH)}' |grep -v ^$ |awk '{if ($2 != 0) print $2}')
    echo $avg_latency
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

