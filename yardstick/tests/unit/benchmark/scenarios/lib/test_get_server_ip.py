##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest

from yardstick.benchmark.scenarios.lib.get_server_ip import GetServerIp


class GetServerIpTestCase(unittest.TestCase):
    def test_get_server_ip(self):
        scenario_cfg = {
            'options': {
                'server': {
                    'addresses': {
                        'net1': [
                            {
                                'OS-EXT-IPS:type': 'floating',
                                'addr': '127.0.0.1'
                            }
                        ]
                    }
                }
            },
            'output': 'ip'
        }
        obj = GetServerIp(scenario_cfg, {})
        result = obj.run({})
        self.assertEqual(result, {'ip': '127.0.0.1'})


def main():
    unittest.main()


if __name__ == '__main__':
    main()
