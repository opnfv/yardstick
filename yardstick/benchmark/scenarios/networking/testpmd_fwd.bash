#!/bin/sh

set -e

# Commandline arguments
DST_MAC=$1         # MAC address of the peer port

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

run_testpmd()
{
    cd /dpdk
    sudo ./destdir/bin/testpmd -c 0x07 -n 4 -b 00:03.0 -- -a --eth-peer=1,$DST_MAC --forward-mode=mac
}

main()
{
    load_modules
    change_permissions
    add_interface_to_dpdk
    run_testpmd
}

main
