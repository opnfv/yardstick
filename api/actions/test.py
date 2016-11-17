import uuid
import json
import logging

from api import conf
from api.utils import common as common_utils

logger = logging.getLogger(__name__)


def runTestCase(args):
    try:
        opts = args.get('opts', {})
        testcase = args['testcase']
    except Exception:
        logger.info('Lack of testcase argument')
        result = {
            'status': 'error',
            'message': 'need testcase name'
        }
        return json.dumps(result)

    testcase = conf.TEST_CASE_PATH + testcase + '.yaml'

    task_id = str(uuid.uuid4())

    command_list = ['task', 'start']
    command_list = common_utils.get_command_list(command_list, opts, testcase)
    logger.info('The command_list is:' + str(command_list))

    logger.info('Start to execute command list')
    common_utils.exec_command_task(command_list, task_id)

    result = {
        'status': 'success',
        'task_id': task_id
    }
    return json.dumps(result)
