#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run yardstick's unit, coverage, functional test

getopts ":f" FILE_OPTION
opts=$@ # get other args

# don't write .pyc files this can cause odd unittest results
export PYTHONDONTWRITEBYTECODE=1

PY_VER="py$( python --version | sed 's/[^[:digit:]]//g' | cut -c-2 )"
export PY_VER

COVER_DIR_NAME="./tools/"
export COVER_DIR_NAME

run_tests() {
    echo "Get external libs needed for unit test"

    echo "Running unittest ... "
    if [ $FILE_OPTION == "f" ]; then
        python -m unittest discover -v -s tests/unit > $logfile 2>&1
        if [ $? -ne 0 ]; then
            echo "FAILED, results in $logfile"
            exit 1
        fi
        python -m unittest discover -v -s yardstick/tests/unit >> $logfile 2>&1
    else
        python -m unittest discover -v -s tests/unit
        if [ $? -ne 0 ]; then
            exit 1
        fi
        python -m unittest discover -v -s yardstick/tests/unit
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
    source $COVER_DIR_NAME/cover.sh
    run_coverage_test
}

run_functional_test() {

    mkdir -p .testrepository
    python -m subunit.run discover yardstick/tests/functional > .testrepository/subunit.log

    subunit2pyunit < .testrepository/subunit.log
    EXIT_CODE=$?
    subunit-stats < .testrepository/subunit.log

    if [ $EXIT_CODE -ne 0 ]; then
        exit 1
    else
        echo "OK"
    fi
}

if [[ $opts =~ "--unit" ]]; then
    run_tests
fi

if [[ $opts =~ "--coverage" ]]; then
    run_coverage
fi

if [[ $opts =~ "--functional" ]]; then
    run_functional_test
fi

if [[ -z $opts ]]; then
    echo "No tests to run!!"
    echo "Usage: run_tests.sh [--unit] [--coverage] [--functional]"
    exit 1
fi
