##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.lib.check_connectivity.CheckConnectivity

from __future__ import absolute_import

import mock
import unittest

from yardstick.benchmark.scenarios.lib import check_connectivity


class CheckConnectivityTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'root',
                'key_filename': 'mykey.key',
                'ssh_port': '22'
            },
            'target': {
                'ipaddr': '172.16.0.138'
            }
        }

    @mock.patch('yardstick.benchmark.scenarios.lib.check_connectivity.ssh')
    def test_check_connectivity(self, mock_ssh):

        args = {
            'options': {'src_ip_addr': '192.168.23.2',
                        'dest_ip_addr': '192.168.23.10',
                        'ssh_user': 'root',
                        'ssh_passwd': 'root',
                        'ssh_port': '22',
                        'ssh_timeout': 600,
                        'ping_parameter': "-s 2048"
                        },
            'sla': {'status': 'True',
                    'action': 'assert'}
        }

        # TODO(elfoley): Properly check the outputs
        result = {}  # pylint: disable=unused-variable

        obj = check_connectivity.CheckConnectivity(args, {})
        obj.setup()
        mock_ssh.SSH.execute.return_value = (0, '100', '')

    @mock.patch('yardstick.benchmark.scenarios.lib.check_connectivity.ssh')
    def test_check_connectivity_key(self, mock_ssh):

        args = {
            'options': {'ssh_user': 'root',
                        'ssh_key': '/root/.ssh/id_rsa',
                        'ssh_port': '22',
                        'ssh_timeout': 600,
                        'ping_parameter': "-s 2048"
                        },
            'sla': {'status': 'True',
                    'action': 'assert'}
        }

        # TODO(elfoley): Properly check the outputs
        result = {}  # pylint: disable=unused-variable

        obj = check_connectivity.CheckConnectivity(args, self.ctx)
        obj.setup()

        mock_ssh.SSH.execute.return_value = (0, '100', '')
