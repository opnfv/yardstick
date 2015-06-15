#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run yardstick's test suite(s)

run_flake8() {
    echo -n "Running flake8 ... "
    logfile=pep8.log
    flake8 yardstick > $logfile
    if [ $? -ne 0 ]; then
        echo "FAILED, result in $logfile"
        exit 1
    else
        echo "OK, result in $logfile"
    fi
}

run_tests() {
    echo -n "Running unittest ... "
    logfile=test.log
    python -m unittest discover -s tests/unit &> $logfile
    if [ $? -ne 0 ]; then
        echo "FAILED, result in $logfile"
        exit 1
    else
        echo "OK, result in $logfile"
    fi
}

run_flake8
run_tests

