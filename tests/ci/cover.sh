#!/bin/bash
##############################################################################
# Copyright 2015: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
# yardstick comment: this is a modified copy of
# rally/tests/ci/cover.sh
##############################################################################

if [[ -n $COVER_DIR_NAME ]]; then
    :
elif [[ -n $_ ]]; then
    COVER_DIR_NAME=$( dirname $_ )
else
    COVER_DIR_NAME=$( dirname $0 )
fi

show_diff () {
    diff -U 0 $1 $2 | awk -f $COVER_DIR_NAME/cover.awk
}

run_coverage_test() {

    ALLOWED_EXTRA_MISSING=10
    # enable debugging
    set -x

    # Stash uncommitted changes, checkout master and save coverage report
    uncommited=$(git status --porcelain | grep -v "^??")
    [[ -n ${uncommited} ]] && git stash > /dev/null
    git checkout HEAD^

    baseline_report=$(mktemp -t yardstick_coverageXXXXXXX)
    ls -l .testrepository

    # workaround 'db type could not be determined' bug
    # https://bugs.launchpad.net/testrepository/+bug/1229445
    rm -rf .testrepository
    find . -type f -name "*.pyc" -delete

    #python setup.py testr --coverage --testr-args=""
    python setup.py testr --coverage --slowest --testr-args="$*"
    testr failing
    coverage report > ${baseline_report}

    # debug awk
    tail -1 ${baseline_report}
    baseline_missing=$(awk 'END { if (int($3) > 0) print $3 }' ${baseline_report})

    if [[ -z $baseline_missing ]]; then
        echo "Failed to determine baseline missing"
        exit 1
    fi

    # Checkout back and unstash uncommitted changes (if any)
    git checkout -
    [[ -n ${uncommited} ]] && git stash pop > /dev/null

    # Generate and save coverage report
    current_report=$(mktemp -t yardstick_coverageXXXXXXX)
    ls -l .testrepository

    # workaround 'db type could not be determined' bug
    # https://bugs.launchpad.net/testrepository/+bug/1229445
    rm -rf .testrepository
    find . -type f -name "*.pyc" -delete

    #python setup.py testr --coverage --testr-args=""
    python setup.py testr --coverage --slowest --testr-args="$*"
    testr failing
    coverage report > ${current_report}

    rm -rf cover-$PY_VER
    coverage html -d cover-$PY_VER

    # debug awk
    tail -1 ${current_report}
    current_missing=$(awk 'END { if (int($3) > 0) print $3 }' ${current_report})

    if [[ -z $current_missing ]]; then
        echo "Failed to determine current missing"
        exit 1
    fi

    # Show coverage details
    new_missing=$((current_missing - baseline_missing))

    echo "Missing lines allowed to introduce : ${ALLOWED_EXTRA_MISSING}"
    echo "Missing lines introduced           : ${new_missing}"
    echo "Missing lines in master            : ${baseline_missing}"
    echo "Missing lines in proposed change   : ${current_missing}"

    if [[ ${new_missing} -gt ${ALLOWED_EXTRA_MISSING} ]];
    then
        show_diff ${baseline_report} ${current_report}
        echo "Please write more unit tests, we should keep our test coverage :( "
        rm ${baseline_report} ${current_report}
        exit 1

    elif [[ ${new_missing} -gt 0 ]];
    then
        show_diff ${baseline_report} ${current_report}
        echo "I believe you can cover all your code with 100% coverage!"

    else
        echo "Thank you! You are awesome! Keep writing unit tests! :)"
    fi

    rm ${baseline_report} ${current_report}
}
