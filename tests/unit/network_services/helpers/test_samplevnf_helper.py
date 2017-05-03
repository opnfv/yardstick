#!/usr/bin/env python

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
#

from __future__ import absolute_import
from __future__ import division
import unittest
import mock
import subprocess

from yardstick.network_services.helpers.samplevnf_helper import \
    OPNFVSampleVNF


class TestOPNFVSampleVNF(unittest.TestCase):

    def test___init__(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            opnfv_vnf = OPNFVSampleVNF(ssh_mock, "/tmp")
            self.assertEqual("/tmp", opnfv_vnf.bin_path)

    def test_deploy_vnfs(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(1, "", ""))
            ssh_mock.put = \
                mock.Mock(return_value=(1, "", ""))
            opnfv_vnf = OPNFVSampleVNF(ssh_mock, "/tmp")
            subprocess.check_output = mock.Mock(return_value=0)
            self.assertEqual(None, opnfv_vnf.deploy_vnfs("vACL"))
