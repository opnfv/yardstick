import unittest
import mock

from api.utils.daemonthread import DaemonThread


class DaemonThreadTestCase(unittest.TestCase):

    @mock.patch('api.utils.daemonthread.os')
    def test_run(self, mock_os):
        def func(common_list, task_id):
            return task_id

        common_list = []
        task_id = '1234'
        thread = DaemonThread(func, (common_list, task_id))
        thread.run()

        mock_os.path.exist.return_value = True
        pre_path = '../tests/opnfv/test_suites/'
        mock_os.remove.assert_called_with(pre_path + '1234.yaml')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
