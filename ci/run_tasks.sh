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

# Execute tasks
echo "Execute sample ping task"
yardstick -d task start samples/ping.yaml

echo "Execute sample iperf3 task"
yardstick -d task start samples/iperf3.yaml

echo "Execute sample pktgen task"
yardstick -d task start samples/pktgen.yaml

echo "Execute sample fio task"
yardstick -d task start samples/fio.yaml

