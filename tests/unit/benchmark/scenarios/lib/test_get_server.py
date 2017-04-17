import unittest
import mock

from yardstick.benchmark.scenarios.lib.get_server import GetServer


class GetServerTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.openstack_utils.get_server_by_name')
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_get_server(self, mock_get_nova_client, mock_get_server_by_name):
        scenario_cfg = {
            'options': {
                'server_name': 'yardstick_server'
            },
            'output': 'status server'
        }
        obj = GetServer(scenario_cfg, {})
        obj.run({})
        self.assertTrue(mock_get_nova_client.called)
        self.assertTrue(mock_get_server_by_name.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
