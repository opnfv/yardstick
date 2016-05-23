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
    modprobe uio
    insmod /dpdk/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    insmod /dpdk/x86_64-native-linuxapp-gcc/kmod/rte_kni.ko
}

change_permissions()
{
    chmod 777 /sys/bus/pci/drivers/virtio-pci/*
    chmod 777 /sys/bus/pci/drivers/igb_uio/*
}

create_dpdk_config_lua()
{
    touch /home/ubuntu/dpdk_cfg.pkt
    cfg_file="/home/ubuntu/dpdk_cfg.pkt"
    chmod 777 $cfg_file

    echo "set ip src 0 ${SRC_IP}/24" > $cfg_file
    echo "set ip dst 0 ${DST_IP}" >> $cfg_file
    echo "set 0 rate 10" >> $cfg_file
    echo 'set 0 size 64' >> $cfg_file
    echo 'process 0 enable' >> $cfg_file
    echo 'start 0' >> $cfg_file
}


load_modules
change_permissions
create_dpdk_config_lua

echo $DST_IP $SRC_IP $NUM_PORTS $PKT_SIZE $DURATION $MAC $DEV> ~/arguments

