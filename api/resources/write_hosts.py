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
from oslo_serialization import jsonutils

from yardstick.common import constants as consts


def write_hosts(hosts_list):
    with open(consts.ETC_HOSTS, 'a') as f:
        f.writelines(hosts_list)


if __name__ == "__main__":
    write_hosts(jsonutils.loads(sys.argv[1]))
