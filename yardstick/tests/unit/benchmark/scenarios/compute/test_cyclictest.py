#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.cyclictest.Cyclictest

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.compute import cyclictest


@mock.patch('yardstick.benchmark.scenarios.compute.cyclictest.ssh')
class CyclictestTestCase(unittest.TestCase):

    def setUp(self):
        self.scenario_cfg = {
            "host": "kvm.LF",
            "setup_options": {
                "rpm_dir": "/opt/rpm",
                "host_setup_seqs": [
                    "host-setup0.sh",
                    "host-setup1.sh",
                    "host-run-qemu.sh"
                ],
                "script_dir": "/opt/scripts",
                "image_dir": "/opt/image",
                "guest_setup_seqs": [
                    "guest-setup0.sh",
                    "guest-setup1.sh"
                ]
            },
            "sla": {
                "action": "monitor",
                "max_min_latency": 50,
                "max_avg_latency": 100,
                "max_max_latency": 1000
            },
            "options": {
                "priority": 99,
                "threads": 1,
                "loops": 1000,
                "affinity": 1,
                "interval": 1000,
                "histogram": 90
            }
        }
        self.context_cfg = {
            "host": {
                "ip": "10.229.43.154",
                "key_filename": "/yardstick/resources/files/yardstick_key",
                "role": "BareMetal",
                "name": "kvm.LF",
                "user": "root"
            }
        }

    def test_cyclictest_successful_setup(self, mock_ssh):

        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        c.setup()
        self.assertIsNotNone(c.guest)
        self.assertIsNotNone(c.host)
        self.assertEqual(c.setup_done, True)

    def test_cyclictest_successful_no_sla(self, mock_ssh):
        result = {}
        self.scenario_cfg.pop("sla", None)
        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        c.guest = mock_ssh.SSH.from_node()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        c.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_cyclictest_successful_sla(self, mock_ssh):
        result = {}
        self.scenario_cfg.update({"sla": {
            "action": "monitor",
            "max_min_latency": 100,
            "max_avg_latency": 500,
            "max_max_latency": 1000
        }
        })
        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        c.guest = mock_ssh.SSH.from_node()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        c.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_cyclictest_unsuccessful_sla_min_latency(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_min_latency": 10}})
        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        c.guest = mock_ssh.SSH.from_node()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, c.run, result)

    def test_cyclictest_unsuccessful_sla_avg_latency(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_avg_latency": 10}})
        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        c.guest = mock_ssh.SSH.from_node()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, c.run, result)

    def test_cyclictest_unsuccessful_sla_max_latency(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_max_latency": 10}})
        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        c.guest = mock_ssh.SSH.from_node()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, c.run, result)

    def test_cyclictest_unsuccessful_script_error(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_max_latency": 10}})
        c = cyclictest.Cyclictest(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        c.setup()

        c.guest = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, c.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
