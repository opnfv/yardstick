##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# make coverage report
##############################################################################

how_diff () {
    head -1 $1
    diff -U 0 $1 $2 | sed 1,2d
}


run_coverage_test() {

    ALLOWED_EXTRA_MISSING=4


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
        exit_code=0
    else
        show_diff $baseline_report $current_report
        echo "Please write more unit tests, we should keep our test coverage :( "
        exit_code=1
    fi

    rm $baseline_report $current_report
    exit $exit_code

}

run_coverage_test
