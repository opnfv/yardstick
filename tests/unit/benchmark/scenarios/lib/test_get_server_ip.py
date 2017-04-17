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
