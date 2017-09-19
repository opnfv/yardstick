from __future__ import absolute_import

import mock
import os
import socket
import unittest
import sys

import tempfile

from oslo_serialization import jsonutils

from yardstick.common import constants as consts


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        consts.SQLITE = 'sqlite:///{}'.format(self.db_path)

        # server calls gethostbyname which takes 4 seconds, and we should mock it anyway
        # we can't mock socket because of greenlet so just by the gethost methods
        self.mock_hostbyname = mock.patch.object(sys.modules['socket'], "gethostbyname",
                                                 return_value="127.0.0.1")
        self.mock_hostname = mock.patch.object(sys.modules['socket'], "gethostname",
                                                 return_value="localhost")
        self.mock_hostbyname.start()
        self.mock_hostname.start()
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
        self.mock_hostbyname.stop()
        self.mock_hostname.stop()

    def _post(self, url, data):
        headers = {'Content-Type': 'application/json'}
        resp = self.app.post(url, data=jsonutils.dumps(data), headers=headers)
        return jsonutils.loads(resp.data)

    def _get(self, url):
        resp = self.app.get(url)
        return jsonutils.loads(resp.data)
