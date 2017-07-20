import os
import logging

import yaml

from api import ApiResource
from yardstick.common.utils import result_handler
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Testsuites(ApiResource):

    def post(self):
        return self._dispatch_post()

    def create_suite(self, args):
        try:
            suite_name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'name must be provided')

        try:
            testcases = args['testcases']
        except KeyError:
            return result_handler(consts.API_ERROR, 'testcases must be provided')

        testcases = [{'file_name': '{}.yaml'.format(t)} for t in testcases]

        suite = os.path.join(consts.TESTSUITE_DIR, '{}.yaml'.format(suite_name))
        suite_content = {
            'schema': 'yardstick:suite:0.1',
            'name': suite_name,
            'test_cases_dir': 'tests/opnfv/test_cases/',
            'test_cases': testcases
        }

        LOG.info('write test suite')
        with open(suite, 'w') as f:
            yaml.dump(suite_content, f, default_flow_style=False)

        return result_handler(consts.API_SUCCESS, {'suite': suite_name})
