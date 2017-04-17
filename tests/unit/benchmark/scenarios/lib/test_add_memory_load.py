import unittest
import mock

from yardstick.benchmark.scenarios.lib.add_memory_load import AddMemoryLoad


class AddMemoryLoadTestCase(unittest.TestCase):

    @mock.patch('yardstick.ssh.SSH.from_node')
    def test_add_memory_load(self, mock_from_node):
        scenario_cfg = {
            'options': {
                'memory_load': 0.5
            }
        }
        context_cfg = {
            'host': {}
        }
        mock_from_node().execute.return_value = (0, '0 2048 512', '')
        obj = AddMemoryLoad(scenario_cfg, context_cfg)
        obj.run({})
        self.assertTrue(mock_from_node.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
