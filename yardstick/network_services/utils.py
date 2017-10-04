# Copyright (c) 2016-2017 Intel Corporation
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
""" Helper function to get Network Service testing configuration """

from __future__ import absolute_import
import logging
import os
import re

from oslo_config import cfg
from oslo_config.cfg import NoSuchOptError
from oslo_utils import encodeutils


NSB_ROOT = "/opt/nsb_bin"

CONF = cfg.CONF
OPTS = [
    cfg.StrOpt('bin_path',
               default=NSB_ROOT,
               help='bin_path for VNFs location.'),
    cfg.StrOpt('trex_path',
               default=os.path.join(NSB_ROOT, 'trex/scripts'),
               help='trex automation lib path.'),
    cfg.StrOpt('trex_client_lib',
               default=os.path.join(NSB_ROOT, 'trex_client/stl'),
               help='trex python library path.'),
]
CONF.register_opts(OPTS, group="nsb")


HEXADECIMAL = "[0-9a-zA-Z]"


class PciAddress(object):
    """Class to handle PCI addresses.

    A PCI address could be written in two ways:
    - Simple BDF notation:
        00:00.0 # bus:device.function
    - With domain extension.
        0000:00:00.0 # domain:bus:device.function

    Note: in Libvirt, 'device' is called 'slot'.

    Reference: https://wiki.xenproject.org/wiki/
               Bus:Device.Function_(BDF)_Notation
    """
    PCI_PATTERN_STR = (
        r"((?P<domain>[0-9a-zA-Z]{4}):)?(?P<bus>[0-9a-zA-Z]{2}):"
        r"(?P<slot>[0-9a-zA-Z]{2})\.(?P<function>[0-9a-zA-Z]{1})")

    def __init__(self, address):
        pci_pattern = re.compile(self.PCI_PATTERN_STR)
        match = pci_pattern.search(address)
        if not match:
            raise ValueError('Invalid PCI address: {}'.format(address))

        self._domain = (match.group('domain') or '0000').lower()
        self._bus = match.group('bus').lower()
        self._slot = match.group('slot').lower()
        self._function = match.group('function').lower()
        self.address = '{:0>4}:{:0>2}:{:0>2}.{:1}'.format(self.domain,
                                                          self.bus,
                                                          self.slot,
                                                          self.function)
        self.match = match

    def __repr__(self):
        return self.address

    @property
    def domain(self):
        return self._domain

    @property
    def bus(self):
        return self._bus

    @property
    def slot(self):
        return self._slot

    @property
    def function(self):
        return self._function

    def values(self):
        return [self._domain, self._bus, self._slot, self._function]


def get_nsb_option(option, default=None):
    """return requested option for yardstick.conf"""

    try:
        return CONF.nsb.__getitem__(option)
    except NoSuchOptError:
        logging.debug("Invalid key %s", option)
    return default


def provision_tool(connection, tool_path, tool_file=None):
    """
    verify if the tool path exits on the node,
    if not push the local binary to remote node

    :return - Tool path
    """
    if not tool_path:
        tool_path = get_nsb_option('tool_path')
    if tool_file:
        tool_path = os.path.join(tool_path, tool_file)
    exit_status = connection.execute("which %s > /dev/null 2>&1" % tool_path)[0]
    if exit_status == 0:
        return encodeutils.safe_decode(tool_path, incoming='utf-8').rstrip()

    logging.warning("%s not found on %s, will try to copy from localhost",
                    tool_path, connection.host)
    bin_path = get_nsb_option("bin_path")
    connection.execute('mkdir -p "%s"' % bin_path)
    connection.put(tool_path, tool_path)
    return tool_path
