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

from datetime import datetime

from api import ApiResource
from api.database.v2.handlers import V2ProjectHandler
from api.database.v2.handlers import V2TaskHandler
from yardstick.common.utils import result_handler
from yardstick.common.utils import change_obj_to_dict
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Projects(ApiResource):

    def get(self):
        project_handler = V2ProjectHandler()
        projects = [change_obj_to_dict(p) for p in project_handler.list_all()]

        for p in projects:
            tasks = p['tasks']
            p['tasks'] = tasks.split(',') if tasks else []

        return result_handler(consts.API_SUCCESS, {'projects': projects})

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


class V2Project(ApiResource):

    def get(self, project_id):
        try:
            uuid.UUID(project_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid project id')

        project_handler = V2ProjectHandler()
        try:
            project = project_handler.get_by_uuid(project_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such project id')

        project_info = change_obj_to_dict(project)
        tasks = project_info['tasks']
        project_info['tasks'] = tasks.split(',') if tasks else []

        return result_handler(consts.API_SUCCESS, {'project': project_info})

    def delete(self, project_id):
        try:
            uuid.UUID(project_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid project id')

        project_handler = V2ProjectHandler()
        try:
            project = project_handler.get_by_uuid(project_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such project id')

        if project.tasks:
            LOG.info('delete related task')
            task_handler = V2TaskHandler()
            for task_id in project.tasks.split(','):
                LOG.debug('delete task: %s', task_id)
                try:
                    task_handler.delete_by_uuid(task_id)
                except ValueError:
                    LOG.exception('no such task id: %s', task_id)

        LOG.info('delete project in database')
        project_handler.delete_by_uuid(project_id)

        return result_handler(consts.API_SUCCESS, {'project': project_id})
