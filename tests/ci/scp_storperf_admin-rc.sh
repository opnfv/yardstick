#!/usr/bin/expect
set timeout 30

spawn scp -o StrictHostKeyChecking=no /root/storperf_admin-rc root@192.168.200.1:/root/storperf_admin-rc
expect "root@192.168.200.1's password: "
send "root\r"
interact
