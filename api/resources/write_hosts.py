##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import

import sys
import json


def write_hosts(hosts_ip):

    yardstick_flag = "# SUT hosts info for Yardstick"
    hosts_list = ('\n{} {} {}'.format(ip, host_name, yardstick_flag)
                  for host_name, ip in hosts_ip.items())

    with open("/etc/hosts", 'r') as f:
        origin_lines = [line for line in f if yardstick_flag not in line]

    with open("/etc/hosts", 'w') as f:
        f.writelines(origin_lines)
        f.write(yardstick_flag)
        f.writelines(hosts_list)


if __name__ == "__main__":
    write_hosts(json.load(sys.stdin))
