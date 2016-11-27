#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import cgitb
import json
import logging
import sys
from itertools import dropwhile, izip_longest
from subprocess import Popen

cgitb.enable(format="text")

logging.basicConfig(level=logging.DEBUG)

OUTPUT_FILE = "/tmp/netperf-out.log"


def run_netperf():
    with open(OUTPUT_FILE, "w") as output_file:
        Popen(["netperf"] + sys.argv[1:], stdout=output_file).wait()


def get_output_selector():
    opt_iter = dropwhile(lambda x: x != '-O', sys.argv[1:])
    # advance to -O
    next(opt_iter)
    return next(opt_iter)


def output_json(selector):
    columns = [c.lower() for c in selector]
    last_line = None
    with open(OUTPUT_FILE) as output_file:
        # only use last line
        for line in output_file:
            last_line = line
    if not last_line:
        raise ValueError("can't find netperf output line")
    fields = last_line.split()
    # add fill value so we can detect field mismatches
    data = dict(izip_longest(columns, fields, fillvalue=""))
    json.dump(data, sys.stdout)

if __name__ == '__main__':
    # parse args first before running test
    output_selector = get_output_selector().split(',')
    run_netperf()
    output_json(output_selector)
