import uuid
import logging

from api import ApiResource
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common.utils import result_handler
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Environments(ApiResource):

    def post(self):
        return self._dispatch_post()

    def create_environment(self, args):
        try:
            name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'name must be provided')

        env_id = str(uuid.uuid4())

        environment_handler = V2EnvironmentHandler()
        env_init_data = {
            'name': name,
            'uuid': env_id
        }
        environment_handler.insert(env_init_data)

        return result_handler(consts.API_SUCCESS, {'uuid': env_id})
