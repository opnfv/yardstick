import logging
import subprocess
import threading

from api import ApiResource
from yardstick.common.utils import result_handler
from yardstick.common.utils import source_env
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class V2Images(ApiResource):

    def post(self):
        return self._dispatch_post()

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
