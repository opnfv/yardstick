##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import mock

from yardstick.benchmark.scenarios.lib.get_numa_info import GetNumaInfo

BASE = 'yardstick.benchmark.scenarios.lib.get_numa_info'


class GetNumaInfoTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.lib.get_numa_info.ET')
    def test_get_numa_info(self, mock_et):
        scenario_cfg = {
            'options': {
                'server': {
                    'id': '1'
                },
                'file': 'yardstick/ssh.py'
            },
            'output': 'numa_info'
        }

        mock_root = mock_et.fromstring('')

        obj = GetNumaInfo(scenario_cfg, {})
        obj._nodes = {}
        obj.make_ssh_client = mock_make_ssh_client = mock.Mock()
        mock_ssh_client = mock_make_ssh_client()
        mock_ssh_client.execute_with_raise.return_value = ''

        with obj:
            obj.run({})

        self.assertEqual(mock_root.iter.call_count, 2)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
