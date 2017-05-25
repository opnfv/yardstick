##############################################################################
# Copyright (c) 2017 Nokia
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
#!/bin/bash

set -e

# Commandline arguments
MOONGEN_PORT1_MAC=$1         # MAC address of the peer port
MOONGEN_PORT2_MAC=$2         # MAC address of the peer port

DPDK_ROOT='/home/ubuntu/vswitchperf/src/dpdk/dpdk'

load_modules()
{
    if ! lsmod | grep "uio" &> /dev/null; then
        modprobe uio
    fi

    if ! lsmod | grep "igb_uio" &> /dev/null; then
        insmod ${DPDK_ROOT}/x86_64-native-linuxapp-gcc/kmod/igb_uio.ko
    fi

    if ! lsmod | grep "rte_kni" &> /dev/null; then
        insmod ${DPDK_ROOT}/x86_64-native-linuxapp-gcc/kmod/rte_kni.ko
    fi
}

change_permissions()
{
    chmod 777 /sys/bus/pci/drivers/virtio-pci/*
    chmod 777 /sys/bus/pci/drivers/igb_uio/*
}

add_interface_to_dpdk(){
    interfaces=$(lspci |grep Eth |tail -n +2 |awk '{print $1}')
    ${DPDK_ROOT}/tools/dpdk-devbind.py --bind=igb_uio $interfaces &> /dev/null
}

run_testpmd()
{
    blacklist=$(lspci |grep Eth |awk '{print $1}'|head -1)
    cd ${DPDK_ROOT}
    sudo ./dpdk/bin/testpmd -c 0x3f -n 4 -b $blacklist -- -a --nb-cores=4 --coremask=0x3c --burst=64 --txd=4096 --rxd=4096 --rxq=2 --txq=2 --rss-udp --eth-peer=0,$MOONGEN_PORT1_MAC --eth-peer=1,$MOONGEN_PORT2_MAC --forward-mode=mac
}

main()
{
    load_modules
    change_permissions
    add_interface_to_dpdk
    run_testpmd
}

main
