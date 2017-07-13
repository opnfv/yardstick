import uuid
import logging

from oslo_serialization import jsonutils

from api import ApiResource
from api.database.v2.models import V2Environment
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common.utils import result_handler
from yardstick.common.utils import change_obj_to_dict
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Environments(ApiResource):

    def get(self):
        environments = [change_obj_to_dict(e) for e in V2Environment.query.all()]

        for e in environments:
            container_info = e['container_id']
            e['container_id'] = jsonutils.loads(container_info) if container_info else {}

        data = {
            'environments': environments
        }

        return result_handler(consts.API_SUCCESS, data)

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
