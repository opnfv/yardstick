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

    PCI_PATTERN_STR = HEXADECIMAL.join([
        "(",
        "{4}):(",  # domain (4 bytes)
        "{2}):(",  # bus (2 bytes)
        "{2}).(",  # function (2 bytes)
        ")",       # slot (1 byte)
    ])

    PCI_PATTERN = re.compile(PCI_PATTERN_STR)

    @classmethod
    def parse_address(cls, text, multi_line=False):
        if multi_line:
            text = text.replace(os.linesep, '')
            match = cls.PCI_PATTERN.search(text)
        return cls(match.group(0))

    def __init__(self, address):
        super(PciAddress, self).__init__()
        match = self.PCI_PATTERN.match(address)
        if not match:
            raise ValueError('Invalid PCI address: {}'.format(address))
        self.address = address
        self.match = match

    def __repr__(self):
        return self.address

    @property
    def domain(self):
        return self.match.group(1)

    @property
    def bus(self):
        return self.match.group(2)

    @property
    def slot(self):
        return self.match.group(3)

    @property
    def function(self):
        return self.match.group(4)

    def values(self):
        return [self.match.group(n) for n in range(1, 5)]


def get_nsb_option(option, default=None):
    """return requested option for yardstick.conf"""

    try:
        return CONF.nsb.__getitem__(option)
    except NoSuchOptError:
        logging.debug("Invalid key %s", option)
    return default


def provision_tool(connection, tool_path, tool_file=None):
    """Push a tool to a remote node.

    Verify if the tool path exits on the node, if not push the local binary to
    the remote node
    """
    if not tool_path:
        tool_path = get_nsb_option('tool_path')
    if tool_file:
        tool_path = os.path.join(tool_path, tool_file)
    if connection.file_exists(tool_path):
        return encodeutils.safe_decode(tool_path, incoming='utf-8').rstrip()

    logging.warning('"%s" not found on %s, will try to copy from localhost',
                    tool_path, connection.host)
    _dir = os.path.dirname(tool_path)
    connection.create_directory(_dir)
    connection.put(tool_path, tool_path)
    return tool_path
