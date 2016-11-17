import json
import logging

from flask import request
from flask_restful import Resource

from api.utils import common as common_utils
from api.actions import test as test_action
from api import conf

logger = logging.getLogger(__name__)


class Test(Resource):
    def post(self):
        action = common_utils.translate_to_str(request.json.get('action', ''))
        args = common_utils.translate_to_str(request.json.get('args', {}))
        logger.debug('Input args is: action: %s, args: %s' % (action, args))

        if action not in conf.TEST_ACTION:
            logger.error('Wrong action')
            result = {
                'status': 'error',
                'message': 'wrong action'
            }
            return json.dumps(result)

        method = getattr(test_action, action)
        return method(args)
