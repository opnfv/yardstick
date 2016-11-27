#!/usr/bin/env python

##############################################################################
# Copyright (c) 2016 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import cgitb
import errno
import logging
import os
import platform
from subprocess import check_call, call

cgitb.enable(format="text")
logging.basicConfig(level=logging.DEBUG)

SOURCES_LIST_D = "/etc/apt/sources.list.d"
REPO_FILE_PATH = os.path.join(SOURCES_LIST_D, "multiverse.list")


def check_for_netperf():
    try:
        call(["netserver", "-V"])
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
    return True


def add_netperf_repos():
    try:
        os.makedirs(SOURCES_LIST_D)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    ubuntu_release_name = platform.dist()[2]
    with open(REPO_FILE_PATH, "w") as repo_file:
        repo_file.write("""\
deb http://archive.ubuntu.com/ubuntu/ {0} main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ {0}-security main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ {0}-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ {0}-proposed main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ {0}-backports main restricted universe multiverse
""".format(ubuntu_release_name))


def remove_netperf_repo():
    try:
        os.remove(REPO_FILE_PATH)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def install_netperf():
    check_call(["apt-get", "update"])
    check_call(
        ["/usr/bin/env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", "netperf"])


def start_netperf():
    ret = call(["pgrep", "netserver"])
    if ret != 0:
        call(["service", "netperf", "start"])


def main():
    if os.geteuid() != 0:
        logging.warning("Must be run as root")
    if not check_for_netperf():
        try:
            add_netperf_repos()
            install_netperf()
        finally:
            remove_netperf_repo()
    start_netperf()


if __name__ == '__main__':
    main()
