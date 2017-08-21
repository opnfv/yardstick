##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import uuid
import yaml
import logging

from oslo_serialization import jsonutils

from api import ApiResource
from api.database.v2.handlers import V2PodHandler
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler
from yardstick.common.task_template import TaskTemplate
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Pods(ApiResource):

    def post(self):
        return self._dispatch_post()

    def upload_pod_file(self, args):
        try:
            upload_file = args['file']
        except KeyError:
            return result_handler(consts.API_ERROR, 'file must be provided')

        try:
            environment_id = args['environment_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'environment_id must be provided')

        try:
            uuid.UUID(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid environment id')

        LOG.info('writing pod file: %s', consts.POD_FILE)
        upload_file.save(consts.POD_FILE)

        with open(consts.POD_FILE) as f:
            data = yaml_load(TaskTemplate.render(f.read()))
        LOG.debug('pod content is: %s', data)

        LOG.info('create pod in database')
        pod_id = str(uuid.uuid4())
        pod_handler = V2PodHandler()
        pod_init_data = {
            'uuid': pod_id,
            'environment_id': environment_id,
            'content': jsonutils.dumps(data)
        }
        pod_handler.insert(pod_init_data)

        LOG.info('update pod in environment')
        environment_handler = V2EnvironmentHandler()
        environment_handler.update_attr(environment_id, {'pod_id': pod_id})

        return result_handler(consts.API_SUCCESS, {'uuid': pod_id, 'pod': data})


class V2Pod(ApiResource):

    def get(self, pod_id):
        try:
            uuid.UUID(pod_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid pod id')

        pod_handler = V2PodHandler()
        try:
            pod = pod_handler.get_by_uuid(pod_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such pod')

        content = jsonutils.loads(pod.content)

        return result_handler(consts.API_SUCCESS, {'pod': content})

    def delete(self, pod_id):
        try:
            uuid.UUID(pod_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid pod id')

        pod_handler = V2PodHandler()
        try:
            pod = pod_handler.get_by_uuid(pod_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such pod')

        LOG.info('update pod in environment')
        environment_handler = V2EnvironmentHandler()
        environment_handler.update_attr(pod.environment_id, {'pod_id': None})

        LOG.info('delete pod in database')
        pod_handler.delete_by_uuid(pod_id)

        return result_handler(consts.API_SUCCESS, {'pod': pod_id})
