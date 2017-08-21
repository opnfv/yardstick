#!/bin/bash

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run yardstick's flake8, unit, coverage, functional test

getopts ":f" FILE_OPTION

# don't write .pyc files this can cause odd unittest results
export PYTHONDONTWRITEBYTECODE=1

PY_VER="py$( python --version | sed 's/[^[:digit:]]//g' | cut -c-2 )"
export PY_VER

COVER_DIR_NAME="./tests/ci/"
export COVER_DIR_NAME

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
    echo "Get external libs needed for unit test"

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
    # don't re-run coverage on both py27 py3, it takes too long
    if [[ -z $SKIP_COVERAGE ]] ; then
        source $COVER_DIR_NAME/cover.sh
        run_coverage_test
    fi
}

run_functional_test() {

    mkdir -p .testrepository
    python -m subunit.run discover tests/functional > .testrepository/subunit.log

    subunit2pyunit < .testrepository/subunit.log
    EXIT_CODE=$?
    subunit-stats < .testrepository/subunit.log

    if [ $EXIT_CODE -ne 0 ]; then
        exit 1
    else
        echo "OK"
    fi
}


run_flake8
run_tests
run_coverage
run_functional_test
