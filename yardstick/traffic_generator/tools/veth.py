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
veth port emulation
"""

import logging
import os

from tools import tasks

_LOGGER = logging.getLogger(__name__)


def add_veth_port(port, peer_port):
    """
    Add a veth port
    :param port:port name for the first port
    :param peer_port: port name for the peer port
    :return: None
    """
    # touch some files in a tmp area so we can track them. This allows us to
    # track VSPerf created veth ports so they can be cleaned up if needed.
    if not os.path.isdir('/tmp/veth'):
        try:
            os.mkdir('/tmp/veth')
        except os.error:
            # OK don't crash but cleanup may be an issue
            _LOGGER.error('Unable to create veth temp folder.')
            _LOGGER.error(
                'Veth ports may not be removed on testcase completion')
    if os.path.isdir('/tmp/veth'):
        with open('/tmp/veth/{}-{}'.format(port, peer_port), 'a'):
            os.utime('/tmp/veth/{}-{}'.format(port, peer_port), None)
    tasks.run_task(['sudo', 'ip', 'link', 'add',
                    port, 'type', 'veth', 'peer', 'name', peer_port],
                   _LOGGER, 'Adding veth port {} with peer port {}...'.format(
                       port, peer_port), False)


def bring_up_eth_port(eth_port, namespace=None):
    """
    Bring up an eth port
    :param eth_port: string of eth port to bring up
    :param namespace: Namespace eth port it located if needed
    :return: None
    """
    if namespace:
        tasks.run_task(['sudo', 'ip', 'netns', 'exec', namespace,
                        'ip', 'link', 'set', eth_port, 'up'],
                       _LOGGER,
                       'Bringing up port {} in namespace {}...'.format(
                           eth_port, namespace), False)
    else:
        tasks.run_task(['sudo', 'ip', 'link', 'set', eth_port, 'up'],
                       _LOGGER, 'Bringing up port...', False)


def del_veth_port(port, peer_port):
    """
    Delete the veth ports, the peer will automatically be deleted on deletion
    of the first port param
    :param port: port name to delete
    :param port: peer port name
    :return: None
    """
    # delete the file if it exists in the temp area
    if os.path.exists('/tmp/veth/{}-{}'.format(port, peer_port)):
        os.remove('/tmp/veth/{}-{}'.format(port, peer_port))
    tasks.run_task(['sudo', 'ip', 'link', 'del', port],
                   _LOGGER, 'Deleting veth port {} with peer {}...'.format(
                       port, peer_port), False)


# pylint: disable=unused-argument
def validate_add_veth_port(result, port, peer_port):
    """
    Validation function for integration testcases
    """
    devs = os.listdir('/sys/class/net')
    return all([port in devs, peer_port in devs])


def validate_bring_up_eth_port(result, eth_port, namespace=None):
    """
    Validation function for integration testcases
    """
    command = list()
    if namespace:
        command += ['ip', 'netns', 'exec', namespace]
    command += ['cat', '/sys/class/net/{}/operstate'.format(eth_port)]
    out = tasks.run_task(command, _LOGGER, 'Validating port up...', False)

    # since different types of ports may report different status the best way
    # we can do this for now is to just make sure it doesn't say down
    if 'down' in out:
        return False
    return True


def validate_del_veth_port(result, port, peer_port):
    """
    Validation function for integration testcases
    """
    devs = os.listdir('/sys/class/net')
    return not any([port in devs, peer_port in devs])
