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

import logging
import os

from six.moves import StringIO

from yardstick.network_services.constants import REMOTE_TMP
from yardstick.ssh import AutoConnectSSH

LOG = logging.getLogger(__name__)


class VnfSshHelper(AutoConnectSSH):

    def __init__(self, node, bin_path, wait=None):
        self.node = node
        kwargs = self.args_from_node(self.node)
        if wait:
            # if wait is defined here we want to override
            kwargs['wait'] = wait

        super(VnfSshHelper, self).__init__(**kwargs)
        self.bin_path = bin_path

    @staticmethod
    def get_class():
        # must return static class name, anything else refers to the calling class
        # i.e. the subclass, not the superclass
        return VnfSshHelper

    def copy(self):
        # this copy constructor is different from SSH classes, since it uses node
        return self.get_class()(self.node, self.bin_path)

    def upload_config_file(self, prefix, content):
        cfg_file = os.path.join(REMOTE_TMP, prefix)
        LOG.debug(content)
        file_obj = StringIO(content)
        self.put_file_obj(file_obj, cfg_file)
        return cfg_file

    def join_bin_path(self, *args):
        return os.path.join(self.bin_path, *args)

    def provision_tool(self, tool_path=None, tool_file=None):
        if tool_path is None:
            tool_path = self.bin_path
        return super(VnfSshHelper, self).provision_tool(tool_path, tool_file)
