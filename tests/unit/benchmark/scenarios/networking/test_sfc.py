#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.networking.sfc

import mock
import unittest

from yardstick.benchmark.scenarios.networking import sfc


class SfcTestCase(unittest.TestCase):

    def setUp(self):
        scenario_cfg = dict()
        context_cfg = dict()

        # Used in Sfc.setup()
        context_cfg['target'] = dict()
        context_cfg['target']['user'] = 'root'
        context_cfg['target']['password'] = 'opnfv'
        context_cfg['target']['ip'] = '127.0.0.1' 

        # Used in Sfc.run()
        context_cfg['host'] = dict()
        context_cfg['host']['user'] = 'root'
        context_cfg['host']['password'] = 'opnfv'
        context_cfg['host']['ip'] = None
        context_cfg['target'] = dict()
        context_cfg['target']['ip'] = '127.0.0.1'

        self.sfc = sfc.Sfc(scenario_cfg=scenario_cfg, context_cfg=context_cfg)

    @mock.patch('yardstick.benchmark.scenarios.networking.sfc.ssh')
    @mock.patch('yardstick.benchmark.scenarios.networking.sfc.sfc_openstack')
    @mock.patch('yardstick.benchmark.scenarios.networking.sfc.subprocess')
    def test_run_for_success(self, mock_subprocess, mock_openstack, mock_ssh):
        # Mock a successfull SSH in Sfc.setup() and Sfc.run()
        mock_ssh.SSH().execute.return_value = (0, '100', '')
        mock_openstack.get_an_IP.return_value = "127.0.0.1"
        mock_subprocess.call.return_value = 'mocked!'

        result = {}
        self.sfc.setup()
        self.sfc.run(result)
        self.sfc.teardown()

    @mock.patch('yardstick.benchmark.scenarios.networking.sfc.ssh')
    @mock.patch('yardstick.benchmark.scenarios.networking.sfc.sfc_openstack')
    @mock.patch('yardstick.benchmark.scenarios.networking.sfc.subprocess')
    def test_run_for_success(self, mock_subprocess, mock_openstack, mock_ssh):
        # Mock a successfull SSH in Sfc.setup() and Sfc.run()
        mock_ssh.SSH().execute.return_value = (0, 'vxlan_tool.py', 'succeeded timed out')
        mock_openstack.get_an_IP.return_value = "127.0.0.1"
        mock_subprocess.call.return_value = 'mocked!'

        result = {}
        self.sfc.setup()
        self.sfc.run(result)
        self.sfc.teardown()


def main():
    unittest.main()

if __name__ == '__main__':
    main()
