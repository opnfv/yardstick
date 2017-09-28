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

# git update using reference as a branch.
# git_update_branch ref
function git_update_branch {
    local git_branch=$1

    git checkout -f origin/${git_branch}
    # a local branch might not exist
    git branch -D ${git_branch} || true
    git checkout -b ${git_branch}
}

# git update using reference as a branch.
# git_update_remote_branch ref
function git_update_remote_branch {
    local git_branch=$1

    git checkout -b ${git_branch} -t origin/${git_branch}
}

# git update using reference as a tag. Be careful editing source at that repo
# as working copy will be in a detached mode
# git_update_tag ref
function git_update_tag {
    local git_tag=$1

    git tag -d ${git_tag}
    # fetching given tag only
    git fetch origin tag ${git_tag}
    git checkout -f ${git_tag}
}


# OpenStack Functions

git_checkout()
{
    local git_ref=$1
    if [[ -n "$(git show-ref refs/tags/${git_ref})" ]]; then
        git_update_tag "${git_ref}"
    elif [[ -n "$(git show-ref refs/heads/${git_ref})" ]]; then
        git_update_branch "${git_ref}"
    elif [[ -n "$(git show-ref refs/remotes/origin/${git_ref})" ]]; then
        git_update_remote_branch "${git_ref}"
    # check to see if it is a remote ref
    elif git fetch --tags origin "${git_ref}"; then
        # refspec / changeset
        git checkout FETCH_HEAD
    else
        # if we are a random commit id we have to unshallow
        # to get all the commits
        git fetch --unshallow origin
        git checkout -f "${git_ref}"
    fi
}

# releng is not needed, we bind-mount the credentials

echo
echo "INFO: Updating yardstick -> ${YARDSTICK_BRANCH}"
if [ ! -d ${YARDSTICK_REPO_DIR} ]; then
    git clone ${YARDSTICK_REPO} ${YARDSTICK_REPO_DIR}
fi
cd ${YARDSTICK_REPO_DIR}
git_checkout ${YARDSTICK_BRANCH}

if [[ "${DEPLOY_SCENARIO:0:2}" == "os" ]];then
    # setup the environment
    source ${YARDSTICK_REPO_DIR}/tests/ci/prepare_env.sh
fi

# execute tests
${YARDSTICK_REPO_DIR}/tests/ci/yardstick-verify $@
