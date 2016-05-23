#!/bin/sh

set -e

# Commandline arguments
DST_IP=$1         # destination IP address
NUM_PORTS=$2      # number of source ports
PKT_SIZE=$3       # packet size
DURATION=$4       # test duration (seconds)
SRC_IP=$5         # destination IP address


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
    /dpdk/tools/dpdk_nic_bind.py --bind=igb_uio 0000:00:03.0
}

create_dpdk_config_lua()
{
    touch /home/ubuntu/startpktgen.lua
    lua_file="/home/ubuntu/startpktgen.lua"
    chmod 777 $lua_file
    echo $lua_file

    cat << EOF > "/home/ubuntu/startpktgen.lua"
package.path = package.path ..";?.lua;test/?.lua;app/?.lua;"

 -- require "Pktgen";
pktSizes = {};
function start_measurement()

  local file = io.open("mes.results","a");
  io.output(file);

  pktgen.set_ipaddr("0", "dst", "$DST_IP");
  pktgen.set_ipaddr("0", "src", "$SRC_IP/24");
  pktgen.set(0, "rate", 100);
  pktgen.set(0, "size", $PKT_SIZE);
  pktgen.set(0, "burst", 32);
  pktgen.process("all", "on");
  pktgen.start(0);

  -- io.write("#Snt(pps)|Rcv(pps)|Miss(pps)|Snt(bps)|Rcv(bps)|Diff(bps) \n");
  sleep($DURATION);

  portRates = pktgen.portStats("all", "rate");
  sent_pkts = portRates[0].pkts_tx;
  io.write(sent_pkts);
  io.write("\n");
  pktgen.stop(0);
  io.close(file);

  end

start_measurement()
EOF
}

run_pktgen()
{
    cd /pktgen-dpdk
    ./app/app/x86_64-native-linuxapp-gcc/pktgen -c 0x07 -n 4 -b 00:04.0 -- -P -m "[1:2].0" -f "/home/ubuntu/startpktgen.lua"
}

echo $DST_IP $SRC_IP $NUM_PORTS $PKT_SIZE $DURATION $MAC $DEV> ~/arguments

load_modules
change_permissions
create_dpdk_config_lua
add_interface_to_dpdk
run_pktgen

