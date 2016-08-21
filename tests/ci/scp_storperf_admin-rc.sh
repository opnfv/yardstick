#!/bin/bash

ssh_options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
sshpass -p root scp 2>/dev/null $ssh_options ~/storperf_admin-rc \
        root@192.168.200.1:/root/ &> /dev/null
