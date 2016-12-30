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

get_external_libs() {
    cd $(dirname ${BASH_SOURCE[0]})
    TREX_DOWNLOAD="https://trex-tgn.cisco.com/trex/release/v2.05.tar.gz"
    TREX_DIR=$PWD/trex/scripts
    if [ ! -d "$TREX_DIR" ]; then
        rm -rf ${TREX_DOWNLOAD##*/}
        if [ ! -e ${TREX_DOWNLOAD##*/} ] ; then
            wget $TREX_DOWNLOAD
        fi
        tar zxvf ${TREX_DOWNLOAD##*/}
        pushd .
        rm -rf trex && mkdir -p trex
        mv v2.05 trex/scripts
        rm -rf v2.05.tar.gz
        touch "$PWD/trex/scripts/automation/trex_control_plane/stl/__init__.py"
        popd
    fi
    echo "Done."
    export PYTHONPATH=$PYTHONPATH:"$PWD/trex/scripts/automation/trex_control_plane"
    export PYTHONPATH=$PYTHONPATH:"$PWD/trex/scripts/automation/trex_control_plane/stl"
    echo $PYTHONPATH
}

run_tests() {
    echo "Get external libs needed for unit test"
    get_external_libs

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
    source tests/ci/cover.sh
    run_coverage_test
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

export PYTHONPATH='yardstick/vTC/apexlake'

run_flake8
run_tests
run_coverage
run_functional_test
