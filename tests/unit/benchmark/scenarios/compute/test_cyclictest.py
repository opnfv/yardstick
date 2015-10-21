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

import mock
import unittest
import json

from yardstick.benchmark.scenarios.compute import cyclictest


@mock.patch('yardstick.benchmark.scenarios.compute.cyclictest.ssh')
class CyclictestTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            "host": {
                "ip": "192.168.50.28",
                "user": "root",
                "key_filename": "mykey.key"
            }
        }

    def test_cyclictest_successful_setup(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        c.setup()

        mock_ssh.SSH().execute.return_value = (0, '', '')
        self.assertIsNotNone(c.client)
        self.assertEqual(c.setup_done, True)

    def test_cyclictest_successful_no_sla(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        options = {
            "affinity": 2,
            "interval": 100,
            "priority": 88,
            "loops": 10000,
            "threads": 2,
            "histogram": 80
        }
        args = {
            "options": options,
        }
        c.server = mock_ssh.SSH()

        sample_output = '{"min": 100, "avg": 500, "max": 1000}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        result = c.run(args)
        expected_result = json.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_cyclictest_successful_sla(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        options = {
            "affinity": 2,
            "interval": 100,
            "priority": 88,
            "loops": 10000,
            "threads": 2,
            "histogram": 80
        }
        sla = {
            "max_min_latency": 100,
            "max_avg_latency": 500,
            "max_max_latency": 1000,
        }
        args = {
            "options": options,
            "sla": sla
        }
        c.server = mock_ssh.SSH()

        sample_output = '{"min": 100, "avg": 500, "max": 1000}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        result = c.run(args)
        expected_result = json.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_cyclictest_unsuccessful_sla_min_latency(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        args = {
            "options": {},
            "sla": {"max_min_latency": 10}
        }
        c.server = mock_ssh.SSH()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'

        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, c.run, args)

    def test_cyclictest_unsuccessful_sla_avg_latency(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        args = {
            "options": {},
            "sla": {"max_avg_latency": 10}
        }
        c.server = mock_ssh.SSH()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'

        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, c.run, args)

    def test_cyclictest_unsuccessful_sla_max_latency(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        args = {
            "options": {},
            "sla": {"max_max_latency": 10}
        }
        c.server = mock_ssh.SSH()
        sample_output = '{"min": 100, "avg": 500, "max": 1000}'

        mock_ssh.SSH().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, c.run, args)

    def test_cyclictest_unsuccessful_script_error(self, mock_ssh):

        c = cyclictest.Cyclictest(self.ctx)
        options = {
            "affinity": 2,
            "interval": 100,
            "priority": 88,
            "loops": 10000,
            "threads": 2,
            "histogram": 80
        }
        sla = {
            "max_min_latency": 100,
            "max_avg_latency": 500,
            "max_max_latency": 1000,
        }
        args = {
            "options": options,
            "sla": sla
        }
        c.server = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, c.run, args)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
