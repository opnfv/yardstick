#!/bin/sh
# source: https://github.com/openstack/neutron/blob/master/tools/coding-checks.sh

set -eu

usage () {
    echo "Usage: $0 [OPTION]..."
    echo "Run Yardstick's coding check(s)"
    echo ""
    echo "  -Y, --pylint [<basecommit>] Run pylint check on the entire neutron module or just files changed in basecommit (e.g. HEAD~1)"
    echo "  -h, --help                  Print this usage message"
    echo
    exit 0
}

process_options () {
    i=1
    while [ $i -le $# ]; do
        eval opt=\$$i
        case $opt in
            -h|--help) usage;;
            -Y|--pylint) pylint=1;;
            *) scriptargs="$scriptargs $opt"
        esac
        i=$((i+1))
    done
}

run_pylint () {
    local target="${scriptargs:-all}"
    local output_format=""

    if [ "$target" = "all" ]; then
        files="ansible api tests yardstick"
    else
        case "$target" in
            *HEAD*|*HEAD~[0-9]*) files=$(git diff --diff-filter=AM --name-only $target -- "*.py");;
            *) echo "$target is an unrecognized basecommit"; exit 1;;
        esac
    fi
    # make Jenkins output parseable because Jenkins doesn't handle color
    # enventually we should use the Jenkins Pylint plugin or other tools
    if [ -n "${BRANCH:-}" ] ; then
        output_format="--output-format=parseable"
    fi
    echo "Running pylint..."
    echo "You can speed this up by running it on 'HEAD~[0-9]' (e.g. HEAD~0, this change only)..."
    if [ -n "${files}" ]; then
        pylint --rcfile=.pylintrc ${output_format} ${files}
    else
        echo "No python changes in this commit, pylint check not required."
        exit 0
    fi
}

scriptargs=
pylint=1

process_options $@

if [ $pylint -eq 1 ]; then
    run_pylint
    exit 0
fi
