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

getopts ":f" FILE_OPTION

run_flake8() {
    echo "Running flake8 ... "
    logfile=test_results.log
    if [ $FILE_OPTION == "f" ]; then
        flake8 yardstick > $logfile
    else
        flake8 yardstick
    fi

    if [ $? -ne 0 ]; then
        echo "FAILED"
        if [ $FILE_OPTION == "f" ]; then
            echo "Results in $logfile"
        fi
        exit 1
    else
        echo "OK"
    fi
}

run_tests() {
    echo "Running unittest ... "
    if [ $FILE_OPTION == "f" ]; then
        python -m unittest discover -v -s tests/unit > $logfile 2>&1
    else
        python -m unittest discover -v -s tests/unit
    fi

    if [ $? -ne 0 ]; then
        if [ $FILE_OPTION == "f" ]; then
            echo "FAILED, results in $logfile"
        fi
        exit 1
    else
        if [ $FILE_OPTION == "f" ]; then
            echo "OK, results in $logfile"
        fi
    fi
}
run_coverage() {
source ./ci/cover.sh
}
run_flake8
run_tests
run_coverage
