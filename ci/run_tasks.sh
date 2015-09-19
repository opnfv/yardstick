#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run yardstick tasks back-to-back
# This script is called from yardstick-{pod} job and decides which tasks
# are executed as part of that job.


# verify that virtual environment is activated
# assumes the virtual environment has been created as described in README.rst
if [[ ! $(which python | grep venv) ]]; then
    echo "Unable to activate venv...Exiting"
    exit 1
fi

EXIT_CODE=0

# Define tasks to be run
TASK_FILE_NAMES[0]='samples/ping.yaml'
TASK_FILE_NAMES[1]='samples/iperf3.yaml'
TASK_FILE_NAMES[2]='samples/pktgen.yaml'
TASK_FILE_NAMES[3]='samples/fio.yaml'
TASK_FILE_NAMES[4]='samples/netperf.yaml'

# Execute tasks
for TASK_FILE in ${TASK_FILE_NAMES[@]}
do
    echo "Executing task from file: $TASK_FILE"
    yardstick -d task start $TASK_FILE

    if [ $? -ne 0 ]; then
        EXIT_CODE=1
    fi
done

exit $EXIT_CODE