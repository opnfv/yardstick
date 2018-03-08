##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import uuid
import logging
import os
import errno
from datetime import datetime

from oslo_serialization import jsonutils

from api import ApiResource
from api.database.v2.handlers import V2TaskHandler
from api.database.v2.handlers import V2ProjectHandler
from api.database.v2.handlers import V2EnvironmentHandler
from api.utils.thread import TaskThread
from yardstick.common.utils import result_handler
from yardstick.common.utils import change_obj_to_dict
from yardstick.common import constants as consts
from yardstick.benchmark.core.task import Task
from yardstick.benchmark.core import Param

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Tasks(ApiResource):

    def get(self):
        task_handler = V2TaskHandler()
        tasks = [change_obj_to_dict(t) for t in task_handler.list_all()]

        for t in tasks:
            result = t['result']
            t['result'] = jsonutils.loads(result) if result else None
            params = t['params']
            t['params'] = jsonutils.loads(params) if params else None

        return result_handler(consts.API_SUCCESS, {'tasks': tasks})

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

        params = task_info['params']
        task_info['params'] = jsonutils.loads(params) if params else None

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
            LOG.info('update tasks in project')
            new_task_list = project.tasks.split(',')
            new_task_list.remove(task_id)
            if new_task_list:
                new_tasks = ','.join(new_task_list)
            else:
                new_tasks = None
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

    def add_params(self, args):
        task_id = args['task_id']
        try:
            params = args['params']
        except KeyError:
            return result_handler(consts.API_ERROR, 'params must be provided')

        LOG.info('update params info in task')

        task_handler = V2TaskHandler()
        task_update_data = {'params': jsonutils.dumps(params)}
        task_handler.update_attr(task_id, task_update_data)

        return result_handler(consts.API_SUCCESS, {'uuid': task_id})

    def add_case(self, args):
        task_id = args['task_id']
        try:
            name = args['case_name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'case_name must be provided')

        try:
            content = args['case_content']
        except KeyError:
            return result_handler(consts.API_ERROR, 'case_content must be provided')

        LOG.info('update case info in task')
        task_handler = V2TaskHandler()
        task_update_data = {
            'case_name': name,
            'content': content,
            'suite': False
        }
        task_handler.update_attr(task_id, task_update_data)

        return result_handler(consts.API_SUCCESS, {'uuid': task_id})

    def add_suite(self, args):
        task_id = args['task_id']
        try:
            name = args['suite_name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'suite_name must be provided')

        try:
            content = args['suite_content']
        except KeyError:
            return result_handler(consts.API_ERROR, 'suite_content must be provided')

        LOG.info('update suite info in task')
        task_handler = V2TaskHandler()
        task_update_data = {
            'case_name': name,
            'content': content,
            'suite': True
        }
        task_handler.update_attr(task_id, task_update_data)

        return result_handler(consts.API_SUCCESS, {'uuid': task_id})

    def run(self, args):
        try:
            task_id = args['task_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'task_id must be provided')

        try:
            uuid.UUID(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid task id')

        task_handler = V2TaskHandler()
        try:
            task = task_handler.get_by_uuid(task_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such task id')

        if not task.environment_id:
            return result_handler(consts.API_ERROR, 'environment not set')

        if not task.case_name or not task.content:
            return result_handler(consts.API_ERROR, 'case not set')

        if task.status == 0:
            return result_handler(consts.API_ERROR, 'task is already running')

        with open('/tmp/{}.yaml'.format(task.case_name), 'w') as f:
            f.write(task.content)

        data = {
            'inputfile': ['/tmp/{}.yaml'.format(task.case_name)],
            'task_id': task_id,
            'task-args': task.params
        }
        if task.suite:
            data.update({'suite': True})

        LOG.info('start task thread')
        param = Param(data)
        task_thread = TaskThread(Task().start, param, task_handler)
        task_thread.start()

        return result_handler(consts.API_SUCCESS, {'uuid': task_id})


class V2TaskLog(ApiResource):

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

        index = int(self._get_args().get('index', 0))

        try:
            with open(os.path.join(consts.TASK_LOG_DIR, '{}.log'.format(task_id))) as f:
                f.seek(index)
                data = f.readlines()
                index = f.tell()
        except OSError as e:
            if e.errno == errno.ENOENT:
                return result_handler(consts.API_ERROR, 'log file does not exist')
            return result_handler(consts.API_ERROR, 'error with log file')

        return_data = {
            'index': index,
            'data': data
        }

        return result_handler(task.status, return_data)
