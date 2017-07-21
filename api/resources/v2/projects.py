import uuid

from datetime import datetime

from api import ApiResource
from api.database.v2.handlers import V2ProjectHandler
from yardstick.common.utils import result_handler
from yardstick.common import constants as consts


class V2Projects(ApiResource):

    def post(self):
        return self._dispatch_post()

    def create_project(self, args):
        try:
            name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'name must be provided')

        project_id = str(uuid.uuid4())
        create_time = datetime.now()
        project_handler = V2ProjectHandler()

        project_init_data = {
            'uuid': project_id,
            'name': name,
            'time': create_time
        }
        project_handler.insert(project_init_data)

        return result_handler(consts.API_SUCCESS, {'uuid': project_id})
