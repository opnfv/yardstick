##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import os
import uuid
import threading
import requests
import datetime

from api import ApiResource
from api.database.v2.handlers import V2ImageHandler
from api.database.v2.handlers import V2EnvironmentHandler
from yardstick.common.utils import result_handler
from yardstick.common.utils import source_env
from yardstick.common import openstack_utils
from yardstick.common.openstack_utils import get_glance_client
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

IMAGE_MAP = {
    'yardstick-image': {
        'path': os.path.join(consts.IMAGE_DIR, 'yardstick-image.img'),
        'url': 'http://artifacts.opnfv.org/yardstick/images/yardstick-image.img'
    },
    'Ubuntu-16.04': {
        'path': os.path.join(consts.IMAGE_DIR, 'xenial-server-cloudimg-amd64-disk1.img'),
        'url': 'cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img'
    },
    'cirros-0.3.5': {
        'path': os.path.join(consts.IMAGE_DIR, 'cirros-0.3.5-x86_64-disk.img'),
        'url': 'http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img'
    }
}


class V2Images(ApiResource):

    def get(self):
        try:
            source_env(consts.OPENRC)
        except OSError:
            return result_handler(consts.API_ERROR, 'source openrc error')

        image_list = openstack_utils.list_images()

        if image_list is False:
            return result_handler(consts.API_ERROR, 'get images error')

        images = {i.name: format_image_info(i) for i in image_list}

        return result_handler(consts.API_SUCCESS, {'status': 1, 'images': images})

    def post(self):
        return self._dispatch_post()

    def load_image(self, args):
        try:
            image_name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'image name must provided')

        if image_name not in IMAGE_MAP:
            return result_handler(consts.API_ERROR, 'wrong image name')

        thread = threading.Thread(target=self._do_load_image, args=(image_name,))
        thread.start()
        return result_handler(consts.API_SUCCESS, {'image': image_name})

    def upload_image(self, args):
        try:
            image_file = args['file']
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

        environment_handler = V2EnvironmentHandler()
        try:
            environment = environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment')

        file_path = os.path.join(consts.IMAGE_DIR, image_file.filename)
        LOG.info('saving file')
        image_file.save(file_path)

        LOG.info('loading image')
        self._load_image(image_file.filename, file_path)

        LOG.info('creating image in DB')
        image_handler = V2ImageHandler()
        image_id = str(uuid.uuid4())
        image_init_data = {
            'uuid': image_id,
            'name': image_file.filename,
            'environment_id': environment_id
        }
        image_handler.insert(image_init_data)

        LOG.info('update image in environment')
        if environment.image_id:
            image_list = environment.image_id.split(',')
            image_list.append(image_id)
            new_image_id = ','.join(image_list)
        else:
            new_image_id = image_id

        environment_handler.update_attr(environment_id, {'image_id': new_image_id})

        return result_handler(consts.API_SUCCESS, {'uuid': image_id})

    def upload_image_by_url(self, args):
        try:
            url = args['url']
        except KeyError:
            return result_handler(consts.API_ERROR, 'url must be provided')

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
            environment = environment_handler.get_by_uuid(environment_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such environment')

        thread = threading.Thread(target=self._do_upload_image_by_url, args=(url,))
        thread.start()

        file_name = url.split('/')[-1]

        LOG.info('creating image in DB')
        image_handler = V2ImageHandler()
        image_id = str(uuid.uuid4())
        image_init_data = {
            'uuid': image_id,
            'name': file_name,
            'environment_id': environment_id
        }
        image_handler.insert(image_init_data)

        LOG.info('update image in environment')
        if environment.image_id:
            image_list = environment.image_id.split(',')
            image_list.append(image_id)
            new_image_id = ','.join(image_list)
        else:
            new_image_id = image_id

        environment_handler.update_attr(environment_id, {'image_id': new_image_id})

        return result_handler(consts.API_SUCCESS, {'uuid': image_id})

    def delete_image(self, args):
        try:
            image_name = args['name']
        except KeyError:
            return result_handler(consts.API_ERROR, 'image name must provided')

        if image_name not in IMAGE_MAP:
            return result_handler(consts.API_ERROR, 'wrong image name')

        glance_client = get_glance_client()
        try:
            image = next((i for i in glance_client.images.list() if i.name == image_name))
        except StopIteration:
            return result_handler(consts.API_ERROR, 'can not find image')

        glance_client.images.delete(image.id)

        return result_handler(consts.API_SUCCESS, {})

    def _do_upload_image_by_url(self, url):
        file_name = url.split('/')[-1]
        path = os.path.join(consts.IMAGE_DIR, file_name)

        LOG.info('download image')
        self._download_image(url, path)

        LOG.info('loading image')
        self._load_image(file_name, path)

    def _do_load_image(self, image_name):
        if not os.path.exists(IMAGE_MAP[image_name]['path']):
            self._download_image(IMAGE_MAP[image_name]['url'],
                                 IMAGE_MAP[image_name]['path'])

        self._load_image(image_name, IMAGE_MAP[image_name]['path'])

    def _load_image(self, image_name, image_path):
        LOG.info('source openrc')
        source_env(consts.OPENRC)

        LOG.info('load image')
        glance_client = get_glance_client()
        image = glance_client.images.create(name=image_name,
                                            visibility='public',
                                            disk_format='qcow2',
                                            container_format='bare')
        with open(image_path, 'rb') as f:
            glance_client.images.upload(image.id, f)

        LOG.info('Done')

    def _download_image(self, url, path):
        start = datetime.datetime.now().replace(microsecond=0)

        LOG.info('download image from: %s', url)
        self._download_file(url, path)

        end = datetime.datetime.now().replace(microsecond=0)
        LOG.info('download image success, total: %s s', end - start)

    def _download_handler(self, start, end, url, filename):

        headers = {'Range': 'bytes=%d-%d' % (start, end)}
        r = requests.get(url, headers=headers, stream=True)

        with open(filename, "r+b") as fp:
            fp.seek(start)
            fp.tell()
            fp.write(r.content)

    def _download_file(self, url, path, num_thread=5):

        r = requests.head(url)
        try:
            file_size = int(r.headers['content-length'])
        except (TypeError, ValueError):
            return

        with open(path, 'wb') as f:
            f.truncate(file_size)

        thread_list = []
        part = file_size // num_thread
        for i in range(num_thread):
            start = part * i
            end = start + part if i != num_thread - 1 else file_size

            kwargs = {'start': start, 'end': end, 'url': url, 'filename': path}
            t = threading.Thread(target=self._download_handler, kwargs=kwargs)
            t.setDaemon(True)
            t.start()
            thread_list.append(t)

        for t in thread_list:
            t.join()


class V2Image(ApiResource):
    def get(self, image_id):
        try:
            uuid.UUID(image_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid image id')

        image_handler = V2ImageHandler()
        try:
            image = image_handler.get_by_uuid(image_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such image id')

        images = openstack_utils.list_images()
        try:
            image = next((i for i in images if i.name == image.name))
        except StopIteration:
            pass

        return_image = format_image_info(image)
        return_image['id'] = image_id

        return result_handler(consts.API_SUCCESS, {'image': return_image})

    def delete(self, image_id):
        try:
            uuid.UUID(image_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'invalid image id')

        image_handler = V2ImageHandler()
        try:
            image = image_handler.get_by_uuid(image_id)
        except ValueError:
            return result_handler(consts.API_ERROR, 'no such image id')

        LOG.info('delete image in openstack')
        glance_client = get_glance_client()
        try:
            image_o = next((i for i in glance_client.images.list() if i.name == image.name))
        except StopIteration:
            return result_handler(consts.API_ERROR, 'can not find image')

        glance_client.images.delete(image_o.id)

        LOG.info('delete image in environment')
        environment_id = image.environment_id
        environment_handler = V2EnvironmentHandler()
        environment = environment_handler.get_by_uuid(environment_id)
        image_list = environment.image_id.split(',')
        image_list.remove(image_id)
        environment_handler.update_attr(environment_id, {'image_id': ','.join(image_list)})

        LOG.info('delete image in DB')
        image_handler.delete_by_uuid(image_id)

        return result_handler(consts.API_SUCCESS, {'image': image_id})


def format_image_info(image):
    image_dict = {}

    if image is None:
        return image_dict

    image_dict['name'] = image.name
    image_dict['size'] = float(image.size) / 1024 / 1024
    image_dict['status'] = image.status.upper()
    image_dict['time'] = image.updated_at

    return image_dict
