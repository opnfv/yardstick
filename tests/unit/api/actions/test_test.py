import unittest
import json

from api.actions import test


class RunTestCase(unittest.TestCase):

    def test_runTestCase_with_no_testcase_arg(self):
        args = {}
        output = json.loads(test.runTestCase(args))

        self.assertEqual('error', output['status'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
