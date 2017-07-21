import uuid
import logging
from datetime import datetime

from api import ApiResource
from api.database.v2.handlers import V2TaskHandler
from api.database.v2.handlers import V2ProjectHandler
from yardstick.common.utils import result_handler
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Tasks(ApiResource):

    def post(self):
        return self._dispatch_post()

    def create_task(self, args):
        try:
            name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'name must be provided')

        try:
            project_id = args['project_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'project_id must be provided')

        task_id = str(uuid.uuid4())
        create_time = datetime.now()
        task_handler = V2TaskHandler()

        LOG.info('create task in database')
        task_init_data = {
            'uuid': task_id,
            'project_id': project_id,
            'name': name,
            'time': create_time,
            'status': -1
        }
        task_handler.insert(task_init_data)

        LOG.info('create task in project')
        project_handler = V2ProjectHandler()
        project_handler.append_attr(project_id, {'tasks': task_id})

        return result_handler(consts.API_SUCCESS, {'uuid': task_id})
