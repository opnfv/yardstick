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

from __future__ import absolute_import

import os
import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.storage import fio


@mock.patch('yardstick.benchmark.scenarios.storage.fio.ssh')
class FioTestCase(unittest.TestCase):

    def setUp(self):
        self.ctx = {
            'host': {
                'ip': '172.16.0.137',
                'user': 'cirros',
                'key_filename': 'mykey.key'
            }
        }
        self.sample_output = {
            'read': 'fio_read_sample_output.json',
            'write': 'fio_write_sample_output.json',
            'rw': 'fio_rw_sample_output.json'
        }

    def test_fio_successful_setup(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {'options': options}
        p = fio.Fio(args, self.ctx)
        p.setup()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_fio_job_file_successful_setup(self, mock_ssh):

        options = {
            'job_file': 'job_file.ini',
            'directory': '/FIO_Test'
        }
        args = {'options': options}
        p = fio.Fio(args, self.ctx)
        p.setup()

        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        self.assertIsNotNone(p.client)
        self.assertEqual(p.setup_done, True)

    def test_fio_successful_no_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {'options': options}
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['rw'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)

        expected_result = '{"read_bw": 83888, "read_iops": 20972,' \
            '"read_lat": 236.8, "write_bw": 84182, "write_iops": 21045,'\
            '"write_lat": 233.55}'
        expected_result = jsonutils.loads(expected_result)
        self.assertEqual(result, expected_result)

    def test_fio_successful_read_no_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': "read",
            'ramp_time': 10
        }
        args = {'options': options}
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['read'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)

        expected_result = '{"read_bw": 36113, "read_iops": 9028,' \
            '"read_lat": 108.7}'
        expected_result = jsonutils.loads(expected_result)
        self.assertEqual(result, expected_result)

    def test_fio_successful_write_no_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'write',
            'ramp_time': 10
        }
        args = {'options': options}
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['write'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)

        expected_result = '{"write_bw": 35107, "write_iops": 8776,'\
            '"write_lat": 111.74}'
        expected_result = jsonutils.loads(expected_result)
        self.assertEqual(result, expected_result)

    def test_fio_successful_lat_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {
            'options': options,
            'sla': {'write_lat': 300.1}
        }
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['rw'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)

        expected_result = '{"read_bw": 83888, "read_iops": 20972,' \
            '"read_lat": 236.8, "write_bw": 84182, "write_iops": 21045,'\
            '"write_lat": 233.55}'
        expected_result = jsonutils.loads(expected_result)
        self.assertEqual(result, expected_result)

    def test_fio_unsuccessful_lat_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {
            'options': options,
            'sla': {'write_lat': 200.1}
        }
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['rw'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_fio_successful_bw_iops_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {
            'options': options,
            'sla': {'read_iops': 20000}
        }
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['rw'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        p.run(result)

        expected_result = '{"read_bw": 83888, "read_iops": 20972,' \
            '"read_lat": 236.8, "write_bw": 84182, "write_iops": 21045,'\
            '"write_lat": 233.55}'
        expected_result = jsonutils.loads(expected_result)
        self.assertEqual(result, expected_result)

    def test_fio_unsuccessful_bw_iops_sla(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {
            'options': options,
            'sla': {'read_iops': 30000}
        }
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        sample_output = self._read_sample_output(self.sample_output['rw'])
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, p.run, result)

    def test_fio_unsuccessful_script_error(self, mock_ssh):

        options = {
            'filename': '/home/ubuntu/data.raw',
            'bs': '4k',
            'rw': 'rw',
            'ramp_time': 10
        }
        args = {'options': options}
        p = fio.Fio(args, self.ctx)
        result = {}

        p.client = mock_ssh.SSH.from_node()

        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, p.run, result)

    def _read_sample_output(self, file_name):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        output = os.path.join(curr_path, file_name)
        with open(output) as f:
            sample_output = f.read()
        return sample_output


def main():
    unittest.main()


if __name__ == '__main__':
    main()
