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
NUM_TRAFFIC_PORTS=${1:-1}

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

run_testpmd()
{
    blacklist=$(lspci |grep Eth |awk '{print $1}'|head -1)
    cd /dpdk
    if [ $NUM_TRAFFIC_PORTS -gt 1 ]; then
        sudo ./destdir/bin/testpmd -c 0x3f -n 4 -b $blacklist -- -a --nb-cores=4 --coremask=0x3c --rxq=2 --rxd=4096 --rss-udp --txq=2 --forward-mode=rxonly
    else
        sudo ./destdir/bin/testpmd -c 0x0f -n 4 -b $blacklist -- -a --nb-cores=2 --coremask=0x0c --rxq=2 --rxd=4096 --rss-udp --txq=2 --forward-mode=rxonly
    fi
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

    run_testpmd
}

main
