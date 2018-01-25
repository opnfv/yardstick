# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re

import pip
from pip import exceptions as pip_exceptions
from pip.operations import freeze

from yardstick.common import privsep


LOG = logging.getLogger(__name__)

ACTION_INSTALL = 'install'
ACTION_UNINSTALL = 'uninstall'


@privsep.yardstick_root.entrypoint
def _pip_main(package, action, target=None):
    if action == ACTION_UNINSTALL:
        cmd = [action, package, '-y']
    elif action == ACTION_INSTALL:
        cmd = [action, package, '--upgrade']
        if target:
            cmd.append('--target=%s' % target)
    return pip.main(cmd)


def _pip_execute_action(package, action=ACTION_INSTALL, target=None):
    """Execute an action with a PIP package.

    According to [1], a package could be a URL, a local directory, a local dist
    file or a requirements file.

    [1] https://pip.pypa.io/en/stable/reference/pip_install/#argument-handling
    """
    try:
        status = _pip_main(package, action, target)
    except pip_exceptions.PipError:
        status = 1

    if not status:
        LOG.info('Action "%s" executed, package %s', package, action)
    else:
        LOG.info('Error executing action "%s", package %s', package, action)
    return status


def pip_remove(package):
    """Remove an installed PIP package"""
    return _pip_execute_action(package, action=ACTION_UNINSTALL)


def pip_install(package, target=None):
    """Install a PIP package"""
    return _pip_execute_action(package, action=ACTION_INSTALL, target=target)


def pip_list(pkg_name=None):
    """Dict of installed PIP packages with version.

    If 'pkg_name' is not None, will return only those packages matching the
    name."""
    pip_regex = re.compile(r"(?P<name>.*)==(?P<version>[\w\.]+)")
    git_regex = re.compile(r".*@(?P<version>[\w]+)#egg=(?P<name>[\w]+)")

    pkg_dict = {}
    for _pkg in freeze.freeze(local_only=True):
        match = pip_regex.match(_pkg) or git_regex.match(_pkg)
        if match and (not pkg_name or (
                pkg_name and match.group('name').find(pkg_name) != -1)):
            pkg_dict[match.group('name')] = match.group('version')

    return pkg_dict
