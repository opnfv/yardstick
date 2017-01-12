import unittest
import mock

from yardstick.cmd.commands.testcase import TestcaseCommands


class TestcaseCommandsUT(unittest.TestCase):
    @mock.patch(
        'yardstick.cmd.commands.testcase.TestcaseCommands._format_print')
    @mock.patch('api.client')
    def test_do_list(self, mock_client, mock_print):
        mock_client.get.return_value = {'result': []}
        TestcaseCommands().do_list({})
        self.assertTrue(mock_print.called)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
