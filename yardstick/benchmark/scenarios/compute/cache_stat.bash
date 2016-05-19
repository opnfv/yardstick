#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run a cachestat cache benchmark in a host

set -e

INTERVAL=$1

run_cachestat()
{
	cd /opt/tempT3/fs/
	./cachestat $INTERVAL
}

main()
{
    # run the test
    run_cachestat
}

main
