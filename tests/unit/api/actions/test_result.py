import unittest
import json

from api.actions import result


class GetResultTestCase(unittest.TestCase):

    def test_getResult_with_no_taskid_arg(self):
        args = {}
        output = json.loads(result.getResult(args))

        self.assertEqual('error', output['status'])


def main():
    unittest.main()


if __name__ == '__main__':
    main()
