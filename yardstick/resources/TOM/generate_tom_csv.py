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
import csv

from api.utils import influx

def get_influx_data(args):
    data = influx.query(args)
    return data

def write_csv(data):
    with open('output.csv', 'wb') as csvfile:
        w = csv.writer(csvfile)
        # Write the header
        fieldnames = data[0].keys()
        w.writerow(fieldnames)
        for row in data:
            w.writerow(row.values())

if __name__ == '__main__':
    data = get_influx_data(sys.argv[1])
    write_csv(data)
