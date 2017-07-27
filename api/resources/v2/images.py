##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import subprocess
import threading

from api import ApiResource
from yardstick.common.utils import result_handler
from yardstick.common.utils import source_env
from yardstick.common.utils import change_obj_to_dict
from yardstick.common.openstack_utils import get_nova_client
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Images(ApiResource):

    def get(self):
        try:
            source_env(consts.OPENRC)
        except:
            return result_handler(consts.API_ERROR, 'source openrc error')

        nova_client = get_nova_client()
        try:
            images_list = nova_client.images.list()
        except:
            return result_handler(consts.API_ERROR, 'get images error')
        else:
            images = [self.get_info(change_obj_to_dict(i)) for i in images_list]
            status = 1 if all(i['status'] == 'ACTIVE' for i in images) else 0
            if not images:
                status = 0

        return result_handler(consts.API_SUCCESS, {'status': status, 'images': images})

    def post(self):
        return self._dispatch_post()

    def get_info(self, data):
        result = {
            'name': data.get('name', ''),
            'size': data.get('OS-EXT-IMG-SIZE:size', ''),
            'status': data.get('status', ''),
            'time': data.get('updated', '')
        }
        return result

    def load_image(self, args):
        thread = threading.Thread(target=self._load_images)
        thread.start()
        return result_handler(consts.API_SUCCESS, {})

    def _load_images(self):
        LOG.info('source openrc')
        source_env(consts.OPENRC)

        LOG.info('clean images')
        cmd = [consts.CLEAN_IMAGES_SCRIPT]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             cwd=consts.REPOS_DIR)
        _, err = p.communicate()
        if p.returncode != 0:
            LOG.error('clean image failed: %s', err)

        LOG.info('load images')
        cmd = [consts.LOAD_IMAGES_SCRIPT]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             cwd=consts.REPOS_DIR)
        _, err = p.communicate()
        if p.returncode != 0:
            LOG.error('load image failed: %s', err)

        LOG.info('Done')
