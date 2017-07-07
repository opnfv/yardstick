#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and other.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.benchmark.scenarios.compute.qemu_migrate.QemuMigrate

from __future__ import absolute_import

import unittest

import mock
from oslo_serialization import jsonutils

from yardstick.benchmark.scenarios.compute import qemu_migrate


@mock.patch('yardstick.benchmark.scenarios.compute.qemu_migrate.ssh')
class QemuMigrateTestCase(unittest.TestCase):

    def setUp(self):
        self.scenario_cfg = {
            "host": "kvm.LF",
            "setup_options": {
                "rpm_dir": "/opt/rpm",
                "script_dir": "/opt/scripts",
                "image_dir": "/opt/image",
                "host_setup_seqs": [
                    "host-setup0.sh",
                    "host-setup1.sh",
                    "setup-ovsdpdk.sh",
                    "host-install-qemu.sh",
                    "host-run-qemu4lm.sh"
                ]
            },
            "sla": {
                "action": "monitor",
                "max_totaltime": 10,
                "max_downtime": 0.10,
                "max_setuptime": 0.50
            },
            "options": {
                "smp": 99,
                "migrate_to_port": 4444,
                "incoming_ip": 0,
                "qmp_src_path": "/tmp/qmp-sock-src",
                "qmp_dst_path": "/tmp/qmp-sock-dst",
                "max_down_time": "0.10"
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

    def test_qemu_migrate_successful_setup(self, mock_ssh):

        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')

        q.setup()
        self.assertIsNotNone(q.host)
        self.assertEqual(q.setup_done, True)

    def test_qemu_migrate_successful_no_sla(self, mock_ssh):
        result = {}
        self.scenario_cfg.pop("sla", None)
        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        q.setup()

        sample_output = '{"totaltime": 15, "downtime": 2, "setuptime": 1}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        q.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_qemu_migrate_successful_sla(self, mock_ssh):
        result = {}
        self.scenario_cfg.update({"sla": {
            "action": "monitor",
            "max_totaltime": 15,
            "max_downtime": 2,
            "max_setuptime": 1
        }
        })
        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        q.setup()

        sample_output = '{"totaltime": 15, "downtime": 2, "setuptime": 1}'
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')

        q.run(result)
        expected_result = jsonutils.loads(sample_output)
        self.assertEqual(result, expected_result)

    def test_qemu_migrate_unsuccessful_sla_totaltime(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_totaltime": 10}})
        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        q.setup()

        sample_output = '{"totaltime": 15, "downtime": 2, "setuptime": 1}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, q.run, result)

    def test_qemu_migrate_unsuccessful_sla_downtime(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_downtime": 0.10}})
        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        q.setup()

        sample_output = '{"totaltime": 15, "downtime": 2, "setuptime": 1}'

        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, q.run, result)

    def test_qemu_migrate_unsuccessful_sla_setuptime(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_setuptime": 0.50}})
        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        q.setup()

        sample_output = '{"totaltime": 15, "downtime": 2, "setuptime": 1}'
   
        mock_ssh.SSH.from_node().execute.return_value = (0, sample_output, '')
        self.assertRaises(AssertionError, q.run, result)

    def test_qemu_migrate_unsuccessful_script_error(self, mock_ssh):

        result = {}
        self.scenario_cfg.update({"sla": {"max_totaltime": 10}})
        q = qemu_migrate.QemuMigrate(self.scenario_cfg, self.context_cfg)
        mock_ssh.SSH.from_node().execute.return_value = (0, '', '')
        q.setup()


        mock_ssh.SSH.from_node().execute.return_value = (1, '', 'FOOBAR')
        self.assertRaises(RuntimeError, q.run, result)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
