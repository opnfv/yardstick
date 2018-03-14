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

from oslo_serialization import jsonutils
from docker import Client
from docker.errors import APIError

from api import ApiResource
from api.database.v2.handlers import V2EnvironmentHandler
from api.database.v2.handlers import V2OpenrcHandler
from api.database.v2.handlers import V2PodHandler
from api.database.v2.handlers import V2ContainerHandler
from yardstick.common.utils import result_handler
from yardstick.common.utils import change_obj_to_dict
from yardstick.common import constants as consts
from yardstick.service.environment import Environment

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Environments(ApiResource):

    def get(self):
        environment_handler = V2EnvironmentHandler()
        environments = [change_obj_to_dict(e) for e in environment_handler.list_all()]

        for e in environments:
            container_info = e['container_id']
            e['container_id'] = jsonutils.loads(container_info) if container_info else {}

            image_id = e['image_id']
            e['image_id'] = image_id.split(',') if image_id else []

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


class V2Environment(ApiResource):

    def get(self, environment_id):
        try:
            uuid.UUID(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid environment id')

        environment_handler = V2EnvironmentHandler()
        try:
            environment = environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment id')

        environment = change_obj_to_dict(environment)

        container_id = environment['container_id']
        environment['container_id'] = jsonutils.loads(container_id) if container_id else {}

        image_id = environment['image_id']
        environment['image_id'] = image_id.split(',') if image_id else []

        return result_handler(consts.API_SUCCESS, {'environment': environment})

    def delete(self, environment_id):
        try:
            uuid.UUID(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid environment id')

        environment_handler = V2EnvironmentHandler()
        try:
            environment = environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment id')

        if environment.openrc_id:
            LOG.info('delete openrc: %s', environment.openrc_id)
            openrc_handler = V2OpenrcHandler()
            openrc_handler.delete_by_uuid(environment.openrc_id)

        if environment.pod_id:
            LOG.info('delete pod: %s', environment.pod_id)
            pod_handler = V2PodHandler()
            pod_handler.delete_by_uuid(environment.pod_id)

        if environment.container_id:
            LOG.info('delete containers')
            container_info = jsonutils.loads(environment.container_id)

            container_handler = V2ContainerHandler()
            client = Client(base_url=consts.DOCKER_URL)
            for k, v in container_info.items():
                LOG.info('start delete: %s', k)
                container = container_handler.get_by_uuid(v)
                LOG.debug('container name: %s', container.name)
                try:
                    client.remove_container(container.name, force=True)
                except APIError:
                    LOG.exception('remove container failed')
                container_handler.delete_by_uuid(v)

        environment_handler.delete_by_uuid(environment_id)

        return result_handler(consts.API_SUCCESS, {'environment': environment_id})


class V2SUT(ApiResource):

    def get(self, environment_id):
        try:
            uuid.UUID(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid environment id')

        environment_handler = V2EnvironmentHandler()
        try:
            environment = environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment id')

        if not environment.pod_id:
            return result_handler(consts.API_SUCCESS, {'sut': {}})

        pod_handler = V2PodHandler()
        try:
            pod = pod_handler.get_by_uuid(environment.pod_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such pod id')
        else:
            pod_content = pod.content

        env = Environment(pod=pod_content)
        sut_info = env.get_sut_info()

        return result_handler(consts.API_SUCCESS, {'sut': sut_info})
