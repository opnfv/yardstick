import unittest
import mock

from yardstick.benchmark.scenarios.lib.check_numa_info import CheckNumaInfo


class CheckNumaInfoTestCase(unittest.TestCase):

    @mock.patch('yardstick.benchmark.scenarios.lib.check_numa_info.CheckNumaInfo._check_vm2_status')
    def test_check_numa_info(self, mock_check_vm2):
        scenario_cfg = {'info1': {}, 'info2': {}}
        obj = CheckNumaInfo(scenario_cfg, {})
        obj.run({})
        self.assertTrue(mock_check_vm2.called)

    def test_check_vm2_status(self):
        info1 = {
            'pinning': [0],
            'vcpupin': [{
                'cpuset': '1,2'
            }]
        }
        info2 = {
            'pinning': [0],
            'vcpupin': [{
                'cpuset': '1,2'
            }]
        }
        scenario_cfg = {'info1': info1, 'info2': info2}
        obj = CheckNumaInfo(scenario_cfg, {})
        status = obj._check_vm2_status(info1, info2)
        self.assertEqual(status, True)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
