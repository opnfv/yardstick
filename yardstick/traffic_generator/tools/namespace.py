# Copyright 2016 Red Hat Corporation.
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


"""
Network namespace emulation
"""

import logging
import os

from tools import tasks

_LOGGER = logging.getLogger(__name__)


def add_ip_to_namespace_eth(port, name, ip_addr, cidr):
    """
    Assign port ip address in namespace
    :param port: port to assign ip to
    :param name: namespace where port resides
    :param ip_addr: ip address in dot notation format
    :param cidr: cidr as string
    :return:
    """
    ip_string = '{}/{}'.format(ip_addr, cidr)
    tasks.run_task(['sudo', 'ip', 'netns', 'exec', name,
                    'ip', 'addr', 'add', ip_string, 'dev', port],
                   _LOGGER, 'Assigning ip to port {}...'.format(port), False)


def assign_port_to_namespace(port, name, port_up=False):
    """
    Assign NIC port to namespace
    :param port: port name as string
    :param name: namespace name as string
    :param port_up: Boolean if the port should be brought up on assignment
    :return: None
    """
    tasks.run_task(['sudo', 'ip', 'link', 'set',
                    'netns', name, 'dev', port],
                   _LOGGER, 'Assigning port {} to namespace {}...'.format(
                       port, name), False)
    if port_up:
        tasks.run_task(['sudo', 'ip', 'netns', 'exec', name,
                        'ip', 'link', 'set', port, 'up'],
                       _LOGGER, 'Bringing up port {}...'.format(port), False)


def create_namespace(name):
    """
    Create a linux namespace. Raises RuntimeError if namespace already exists
    in the system.
    :param name: name of the namespace to be created as string
    :return: None
    """
    if name in get_system_namespace_list():
        raise RuntimeError('Namespace already exists in system')

    # touch some files in a tmp area so we can track them separately from
    # the OS's internal namespace tracking. This allows us to track VSPerf
    # created namespaces so they can be cleaned up if needed.
    if not os.path.isdir('/tmp/namespaces'):
        try:
            os.mkdir('/tmp/namespaces')
        except os.error:
            # OK don't crash, but cleanup may be an issue...
            _LOGGER.error('Unable to create namespace temp folder.')
            _LOGGER.error(
                'Namespaces will not be removed on test case completion')
    if os.path.isdir('/tmp/namespaces'):
        with open('/tmp/namespaces/{}'.format(name), 'a'):
            os.utime('/tmp/namespaces/{}'.format(name), None)

    tasks.run_task(['sudo', 'ip', 'netns', 'add', name], _LOGGER,
                   'Creating namespace {}...'.format(name), False)
    tasks.run_task(['sudo', 'ip', 'netns', 'exec', name,
                    'ip', 'link', 'set', 'lo', 'up'], _LOGGER,
                   'Enabling loopback interface...', False)


def delete_namespace(name):
    """
    Delete linux network namespace
    :param name: namespace to delete
    :return: None
    """
    # delete the file if it exists in the temp area
    if os.path.exists('/tmp/namespaces/{}'.format(name)):
        os.remove('/tmp/namespaces/{}'.format(name))
    tasks.run_task(['sudo', 'ip', 'netns', 'delete', name], _LOGGER,
                   'Deleting namespace {}...'.format(name), False)


def get_system_namespace_list():
    """
    Return tuple of strings for namespaces on the system
    :return: tuple of namespaces as string
    """
    return tuple(os.listdir('/var/run/netns')) if os.path.exists(
        '/var/run/netns') else tuple()

def get_vsperf_namespace_list():
    """
    Return a tuple of strings for namespaces created by vsperf testcase
    :return: tuple of namespaces as string
    """
    if os.path.isdir('/tmp/namespaces'):
        return tuple(os.listdir('/tmp/namespaces'))
    else:
        return []


def reset_port_to_root(port, name):
    """
    Return the assigned port to the root namespace
    :param port: port to return as string
    :param name: namespace the port currently resides
    :return: None
    """
    tasks.run_task(['sudo', 'ip', 'netns', 'exec', name,
                    'ip', 'link', 'set', port, 'netns', '1'],
                   _LOGGER, 'Assigning port {} to namespace {}...'.format(
                       port, name), False)


# pylint: disable=unused-argument
# pylint: disable=invalid-name
def validate_add_ip_to_namespace_eth(result, port, name, ip_addr, cidr):
    """
    Validation function for integration testcases
    """
    ip_string = '{}/{}'.format(ip_addr, cidr)
    return ip_string in ''.join(tasks.run_task(
        ['sudo', 'ip', 'netns', 'exec', name, 'ip', 'addr', 'show', port],
        _LOGGER, 'Validating ip address in namespace...', False))


def validate_assign_port_to_namespace(result, port, name, port_up=False):
    """
    Validation function for integration testcases
    """
    # this could be improved...its not 100% accurate
    return port in ''.join(tasks.run_task(
        ['sudo', 'ip', 'netns', 'exec', name, 'ip', 'addr'],
        _LOGGER, 'Validating port in namespace...'))


def validate_create_namespace(result, name):
    """
    Validation function for integration testcases
    """
    return name in get_system_namespace_list()


def validate_delete_namespace(result, name):
    """
    Validation function for integration testcases
    """
    return name not in get_system_namespace_list()


def validate_reset_port_to_root(result, port, name):
    """
    Validation function for integration testcases
    """
    return not validate_assign_port_to_namespace(result, port, name)
