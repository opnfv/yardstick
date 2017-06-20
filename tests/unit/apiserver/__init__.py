from __future__ import absolute_import

import os
import socket
import unittest
import tempfile

from oslo_serialization import jsonutils

from yardstick.common import constants as consts


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        consts.SQLITE = 'sqlite:///{}'.format(self.db_path)

        try:
            from api import server
        except socket.gaierror:
            self.app = None
            return

        server.app.config['TESTING'] = True
        self.app = server.app.test_client()

        server.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _post(self, url, data):
        headers = {'Content-Type': 'application/json'}
        resp = self.app.post(url, data=jsonutils.dumps(data), headers=headers)
        return jsonutils.loads(resp.data)

    def _get(self, url):
        resp = self.app.get(url)
        return jsonutils.loads(resp.data)
