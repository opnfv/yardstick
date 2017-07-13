import uuid
import logging
import re
import os

import yaml
from oslo_serialization import jsonutils

from api import ApiResource
from api.database.v2.handlers import V2OpenrcHandler
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common import constants as consts
from yardstick.common.utils import result_handler
from yardstick.common.utils import makedirs
from yardstick.common.utils import source_env

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Openrc(ApiResource):

    def post(self):
        return self._dispatch_post()

    def upload_openrc(self, args):
        try:
            upload_file = args['file']
        except KeyError:
            return result_handler(consts.API_ERROR, 'file must be provided')

        try:
            environment_id = args['environment_id']
        except KeyError:
            return result_handler(consts.API_ERROR, 'environment_id must be provided')

        LOG.info('writing openrc: %s', consts.OPENRC)
        makedirs(consts.CONF_DIR)
        upload_file.save(consts.OPENRC)
        source_env(consts.OPENRC)

        LOG.info('parsing openrc')
        try:
            openrc_data = self._get_openrc_dict()
        except Exception:
            LOG.exception('parse openrc failed')
            return result_handler(consts.API_ERROR, 'parse openrc failed')

        openrc_id = str(uuid.uuid4())
        self._write_into_database(environment_id, openrc_id, openrc_data)

        LOG.info('writing ansible cloud conf')
        try:
            self._generate_ansible_conf_file(openrc_data)
        except Exception:
            LOG.exception('write cloud conf failed')
            return result_handler(consts.API_ERROR, 'genarate ansible conf failed')
        LOG.info('finish writing ansible cloud conf')

        return result_handler(consts.API_SUCCESS, {'openrc': openrc_data, 'uuid': openrc_id})

    def _write_into_database(self, environment_id, openrc_id, openrc_data):
        LOG.info('writing openrc to database')
        openrc_handler = V2OpenrcHandler()
        openrc_init_data = {
            'uuid': openrc_id,
            'environment_id': environment_id,
            'content': jsonutils.dumps(openrc_data)
        }
        openrc_handler.insert(openrc_init_data)

        LOG.info('binding openrc to environment: %s', environment_id)
        environment_handler = V2EnvironmentHandler()
        environment_handler.update_attr(environment_id, {'openrc_id': openrc_id})

    def _get_openrc_dict(self):
        with open(consts.OPENRC) as f:
            content = f.readlines()

        result = {}
        for line in content:
            m = re.search(r'(\ .*)=(.*)', line)
            if m:
                try:
                    value = os.environ[m.group(1).strip()]
                except KeyError:
                    pass
                else:
                    result.update({m.group(1).strip(): value})

        return result

    def _generate_ansible_conf_file(self, openrc_data):
        ansible_conf = {
            'clouds': {
                'opnfv': {
                    'auth': {
                    }
                }
            }
        }
        black_list = ['OS_IDENTITY_API_VERSION', 'OS_IMAGE_API_VERSION']

        for k, v in openrc_data.items():
            if k.startswith('OS') and k not in black_list:
                key = k[3:].lower()
                ansible_conf['clouds']['opnfv']['auth'][key] = v

        try:
            value = openrc_data['OS_IDENTITY_API_VERSION']
        except KeyError:
            pass
        else:
            ansible_conf['clouds']['opnfv']['identity_api_version'] = value

        makedirs(consts.OPENSTACK_CONF_DIR)
        with open(consts.CLOUDS_CONF, 'w') as f:
            yaml.dump(ansible_conf, f, default_flow_style=False)
