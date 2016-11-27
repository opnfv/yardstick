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
import logging
from subprocess import call

cgitb.enable(format="text")
logging.basicConfig(level=logging.DEBUG)


def main():
    logging.info("Remove netperf after test")
    call(["service", "netperf", "stop"])
    call(["apt-get", "purge", "-y", "netperf"])
    logging.info("netperf purged")
