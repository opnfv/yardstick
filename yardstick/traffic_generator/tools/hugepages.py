# Copyright 2015-2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Automation of hugepages management
"""

import os
import re
import subprocess
import logging
import locale
import math

from yardstick.traffic_generator.tools import tasks
from yardstick.traffic_generator.conf import settings

_LOGGER = logging.getLogger(__name__)
_ALLOCATED_HUGEPAGES = False
#
# hugepage management
#


def get_hugepage_size():
    """Return the size of the configured hugepages
    """
    hugepage_size_re = re.compile(r'^Hugepagesize:\s+(?P<size_hp>\d+)\s+kB',
                                  re.IGNORECASE)
    with open('/proc/meminfo', 'r') as result_file:
        data = result_file.readlines()
        for line in data:
            match = hugepage_size_re.search(line)
            if match:
                _LOGGER.info('Hugepages size: %s kb', match.group('size_hp'))
                return int(match.group('size_hp'))
        _LOGGER.error('Could not parse for hugepage size')
        return 0


def allocate_hugepages():
    """Allocate hugepages on the fly
    """
    hp_size = get_hugepage_size()
    if hp_size > 0:
        nr_hp = int(math.ceil(settings.getValue('HUGEPAGE_RAM_ALLOCATION')/hp_size))
        _LOGGER.info('Will allocate %s hugepages.', nr_hp)

        nr_hugepages = 'vm.nr_hugepages=' + str(nr_hp)
        try:
            tasks.run_task(['sudo', 'sysctl', nr_hugepages],
                           _LOGGER, 'Trying to allocate hugepages..', True)
        except subprocess.CalledProcessError:
            _LOGGER.error('Unable to allocate hugepages.')
            return False
        # pylint: disable=global-statement
        global _ALLOCATED_HUGEPAGES
        _ALLOCATED_HUGEPAGES = True
        return True

    else:
        _LOGGER.error('Division by 0 will be supported in next release')
        return False

def deallocate_hugepages():
    """De-allocate hugepages that were allocated on the fly
    """
    # pylint: disable=global-statement
    global _ALLOCATED_HUGEPAGES
    if _ALLOCATED_HUGEPAGES:
        nr_hugepages = 'vm.nr_hugepages= 0'
        try:
            tasks.run_task(['sudo', 'sysctl', nr_hugepages],
                           _LOGGER, 'Trying to de-allocate hugepages..', True)
        except subprocess.CalledProcessError:
            _LOGGER.error('Unable to de-allocate hugepages.')
            return False
        _ALLOCATED_HUGEPAGES = False
    return True


def get_free_hugepages(socket=None):
    """Get the free hugepage totals on the system.

    :param socket: optional socket param to get free hugepages on a socket. To
                   be passed a string.
    :returns: hugepage amount as int
    """
    hugepage_free_re = re.compile(r'HugePages_Free:\s+(?P<free_hp>\d+)$')
    if socket:
        if os.path.exists(
                '/sys/devices/system/node/node{}/meminfo'.format(socket)):
            meminfo_path = '/sys/devices/system/node/node{}/meminfo'.format(
                socket)
        else:
            _LOGGER.info('No hugepage info found for socket %s', socket)
            return 0
    else:
        meminfo_path = '/proc/meminfo'

    with open(meminfo_path, 'r') as result_file:
        data = result_file.readlines()
        for line in data:
            match = hugepage_free_re.search(line)
            if match:
                _LOGGER.info('Hugepages free: %s %s', match.group('free_hp'),
                             'on socket {}'.format(socket) if socket else '')
                return int(match.group('free_hp'))
        _LOGGER.info('Could not parse for hugepage size')
        return 0


def is_hugepage_available():
    """Check if hugepages are configured/available on the system.
    """
    hugepage_size_re = re.compile(r'^Hugepagesize:\s+(?P<size_hp>\d+)\s+kB',
                                  re.IGNORECASE)

    # read in meminfo
    with open('/proc/meminfo') as mem_file:
        mem_info = mem_file.readlines()

    # see if the hugepage size is the recommended value
    for line in mem_info:
        match_size = hugepage_size_re.match(line)
        if match_size:
            if match_size.group('size_hp') != '1048576':
                _LOGGER.info(
                    '%s%s%s kB',
                    'Hugepages not configured for recommend 1GB size. ',
                    'Currently set at ', match_size.group('size_hp'))
    num_huge = get_free_hugepages()
    if num_huge == 0:
        _LOGGER.info('No free hugepages.')
        if not allocate_hugepages():
            return False
    else:
        _LOGGER.info('Found \'%s\' free hugepage(s).', num_huge)
    return True


def is_hugepage_mounted():
    """Check if hugepages are mounted.
    """
    output = subprocess.check_output(['mount'], shell=True)
    my_encoding = locale.getdefaultlocale()[1]
    for line in output.decode(my_encoding).split('\n'):
        if 'hugetlbfs' in line:
            return True

    return False


def mount_hugepages():
    """Ensure hugepages are mounted. Raises RuntimeError if no configured
    hugepages are available.
    """
    if not is_hugepage_available():
        raise RuntimeError('No Hugepages configured.')

    if is_hugepage_mounted():
        return

    if not os.path.exists(settings.getValue('HUGEPAGE_DIR')):
        tasks.run_task(['sudo', 'mkdir', settings.getValue('HUGEPAGE_DIR')], _LOGGER,
                       'Creating directory ' + settings.getValue('HUGEPAGE_DIR'), True)
    try:
        tasks.run_task(['sudo', 'mount', '-t', 'hugetlbfs', 'nodev',
                        settings.getValue('HUGEPAGE_DIR')],
                       _LOGGER, 'Mounting hugepages...', True)
    except subprocess.CalledProcessError:
        _LOGGER.error('Unable to mount hugepages.')


def umount_hugepages():
    """Ensure hugepages are unmounted.
    """
    if not is_hugepage_mounted():
        return

    try:
        tasks.run_task(['sudo', 'umount', settings.getValue('HUGEPAGE_DIR')],
                       _LOGGER, 'Unmounting hugepages...', True)
    except subprocess.CalledProcessError:
        _LOGGER.error('Unable to umount hugepages.')

    if not deallocate_hugepages():
        _LOGGER.error('Unable to deallocate previously allocated hugepages.')
