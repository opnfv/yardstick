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

from oslo_config import cfg
from oslo_config.cfg import NoSuchOptError
from oslo_utils import encodeutils

CONF = cfg.CONF
OPTS = [
    cfg.StrOpt('bin_path',
               default='/opt/nsb_bin',
               help='bin_path for VNFs location.'),
    cfg.StrOpt('trex_path',
               default='/opt/nsb_bin/trex/scripts',
               help='trex automation lib pathh.'),
]
CONF.register_opts(OPTS, group="nsb")


def get_nsb_option(option, default=None):
    """return requested option for yardstick.conf"""

    try:
        return CONF.nsb.__getitem__(option)
    except NoSuchOptError:
        logging.debug("Invalid key %s", option)
    else:
        return default


def provision_tool(connection, tool_path):
    """
    verify if the tool path exits on the node,
    if not push the local binary to remote node

    :return - Tool path
    """
    bin_path = get_nsb_option("bin_path")
    exit_status, stdout = connection.execute("which %s" % tool_path)[:2]
    if exit_status == 0:
        return encodeutils.safe_decode(stdout, incoming='utf-8').rstrip()

    logging.warning("%s not found on %s, will try to copy from localhost",
                    tool_path, connection.host)
    connection.execute('mkdir -p "%s"' % bin_path)
    connection.put(tool_path, tool_path)
    return tool_path
