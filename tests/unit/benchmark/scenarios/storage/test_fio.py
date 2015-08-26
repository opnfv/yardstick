#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.storage.fio.Fio

import mock
import unittest
import json

from yardstick.benchmark.scenarios.storage import fio


@mock.patch('yardstick.benchmark.scenarios.storage.fio.ssh')
class FioTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': '172.16.0.137',
            'user': 'cirros',
            'key_filename': "mykey.key"
        }

    def test_fio_successful_setup(self, mock_ssh):

        p = fio.Fio(self.ctx)
        options = {
            'filename': "/home/ec2-user/data.raw",
            'bs': "4k",
            'rw': "write",
            'ramp_time': 10
        }
        args = {'options': options}
        p.setup()

        mock_ssh.SSH().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_fio_successful_no_sla(self, mock_ssh):

        p = fio.Fio(self.ctx)
        options = {
            'filename': "/home/ec2-user/data.raw",
            'bs': "4k",
            'rw': "write",
            'ramp_time': 10
        }
        args = {'options': options}
        p.client = mock_ssh.SSH()

        sample_output = '{"read_bw": "N/A", "write_lat": "407.08usec", \
            "read_iops": "N/A", "write_bw": "9507KB/s", \
            "write_iops": "2376", "read_lat": "N/A"}'
        mock_ssh.SSH().execute.return_value = (0, sample_output, '')

        result = p.run(args)
        expected_result = json.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_fio_unsuccessful_script_error(self, mock_ssh):

        p = fio.Fio(self.ctx)
        options = {
            'filename': "/home/ec2-user/data.raw",
            'bs': "4k",
            'rw': "write",
            'ramp_time': 10
        }
        args = {'options': options}
        p.client = mock_ssh.SSH()

        mock_ssh.SSH().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, args)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
