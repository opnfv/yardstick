#!/bin/bash
##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

: ${YARDSTICK_REPO:='https://gerrit.opnfv.org/gerrit/yardstick'}
: ${YARDSTICK_REPO_DIR:='/home/opnfv/repos/yardstick'}
: ${YARDSTICK_BRANCH:='master'} # branch, tag, sha1 or refspec

: ${RELENG_REPO:='https://gerrit.opnfv.org/gerrit/releng'}
: ${RELENG_REPO_DIR:='/home/opnfv/repos/releng'}
: ${RELENG_BRANCH:='master'} # branch, tag, sha1 or refspec

git_checkout()
{
    if git cat-file -e $1^{commit} 2>/dev/null; then
        # branch, tag or sha1 object
        git checkout $1
    else
        # refspec / changeset
        git fetch --tags --progress $2 $1
        git checkout FETCH_HEAD
    fi
}

echo
echo "INFO: Updating releng -> $RELENG_BRANCH"
if [ ! -d $RELENG_REPO_DIR ]; then
    git clone $RELENG_REPO $RELENG_REPO_DIR
fi
cd $RELENG_REPO_DIR
git checkout master
git_checkout $RELENG_BRANCH $RELENG_REPO

echo
echo "INFO: Updating yardstick -> $YARDSTICK_BRANCH"
if [ ! -d $YARDSTICK_REPO_DIR ]; then
    git clone $YARDSTICK_REPO $YARDSTICK_REPO_DIR
fi
cd $YARDSTICK_REPO_DIR
git_checkout $YARDSTICK_BRANCH $YARDSTICK_REPO

# setup the environment
source $YARDSTICK_REPO_DIR/tests/ci/prepare_env.sh

# execute tests
$YARDSTICK_REPO_DIR/tests/ci/yardstick-verify $@
