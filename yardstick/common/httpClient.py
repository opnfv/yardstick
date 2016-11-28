import json
import logging

import requests

logger = logging.getLogger(__name__)


class HttpClient(object):

    def post(self, url, data):
        data = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, data=data, headers=headers)
            result = response.json()
            if result.get('status', '') != 'success':
                message = 'Failed: %s' % result.get('message', '')
                print message
                logger.debug(message)
        except Exception as e:
            logger.debug('Failed: %s', e)
