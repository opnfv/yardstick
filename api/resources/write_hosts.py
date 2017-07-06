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
    hosts_list = ('\n{} {}'.format(ip, host_name)
                  for host_name, ip in hosts_ip.items())
    with open("/etc/hosts", 'a') as f:
        f.writelines(hosts_list)
        f.write("\n")

if __name__ == "__main__":
    write_hosts(json.load(sys.stdin))
