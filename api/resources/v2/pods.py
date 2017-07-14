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
            data = yaml.safe_load(TaskTemplate.render(f.read()))
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
