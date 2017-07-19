import uuid
import logging
from datetime import datetime

from oslo_serialization import jsonutils

from api import ApiResource
from api.database.v2.handlers import V2TaskHandler
from api.database.v2.handlers import V2ProjectHandler
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common.utils import result_handler
from yardstick.common.utils import change_obj_to_dict
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


class V2Task(ApiResource):

    def get(self, task_id):
        try:
            uuid.UUID(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task id')

        task_handler = V2TaskHandler()
        try:
            task = task_handler.get_by_uuid(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such task id')

        task_info = change_obj_to_dict(task)
        result = task_info['result']
        task_info['result'] = jsonutils.loads(result) if result else None

        return result_handler(consts.API_SUCCESS, {'task': task_info})

    def delete(self, task_id):
        try:
            uuid.UUID(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task id')

        task_handler = V2TaskHandler()
        try:
            project_id = task_handler.get_by_uuid(task_id).project_id
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such task id')

        LOG.info('delete task in database')
        task_handler.delete_by_uuid(task_id)

        project_handler = V2ProjectHandler()
        project = project_handler.get_by_uuid(project_id)

        if project.tasks:
            new_tasks = ','.join(project.tasks.split(',').remove(task_id))
            project_handler.update_attr(project_id, {'tasks': new_tasks})

        return result_handler(consts.API_SUCCESS, {'task': task_id})

    def put(self, task_id):

        try:
            uuid.UUID(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task id')

        task_handler = V2TaskHandler()
        try:
            task_handler.get_by_uuid(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such task id')

        return self._dispatch_post(task_id=task_id)

    def add_environment(self, args):

        task_id = args['task_id']
        try:
            environment_id = args['environment_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'environment_id must be provided')

        try:
            uuid.UUID(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid environment id')

        environment_handler = V2EnvironmentHandler()
        try:
            environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment id')

        LOG.info('update environment_id in task')
        task_handler = V2TaskHandler()
        task_handler.update_attr(task_id, {'environment_id': environment_id})

        return result_handler(consts.API_SUCCESS, {'uuid': task_id})
