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

show_diff () {
    head -1 $1
    diff -U 0 $1 $2 | sed 1,2d
}


run_coverage_test() {

    ALLOWED_EXTRA_MISSING=10


    # Stash uncommitted changes, checkout master and save coverage report
    uncommited=$(git status --porcelain | grep -v "^??")
    [[ -n $uncommited ]] && git stash > /dev/null
    git checkout HEAD^

    baseline_report=$(mktemp -t yardstick_coverageXXXXXXX)
    find . -type f -name "*.pyc" -delete && python setup.py testr --coverage --testr-args="$*"
    coverage report > $baseline_report
    baseline_missing=$(awk 'END { print $3 }' $baseline_report)

    # Checkout back and unstash uncommitted changes (if any)
    git checkout -
    [[ -n $uncommited ]] && git stash pop > /dev/null

    # Generate and save coverage report
    current_report=$(mktemp -t yardstick_coverageXXXXXXX)
    find . -type f -name "*.pyc" -delete && python setup.py testr --coverage --testr-args="$*"
    coverage report > $current_report
    current_missing=$(awk 'END { print $3 }' $current_report)

    # Show coverage details
    allowed_missing=$((baseline_missing+ALLOWED_EXTRA_MISSING))

    echo "Allowed to introduce missing lines : ${ALLOWED_EXTRA_MISSING}"
    echo "Missing lines in master            : ${baseline_missing}"
    echo "Missing lines in proposed change   : ${current_missing}"

    if [ $allowed_missing -gt $current_missing ];
    then
        if [ $baseline_missing -lt $current_missing ];
        then
            show_diff $baseline_report $current_report
            echo "I believe you can cover all your code with 100% coverage!"
        else
            echo "Thank you! You are awesome! Keep writing unit tests! :)"
        fi
    else
        show_diff $baseline_report $current_report
        echo "Please write more unit tests, we should keep our test coverage :( "
        rm $baseline_report $current_report
        exit 1
    fi

    rm $baseline_report $current_report
}
