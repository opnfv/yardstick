##############################################################################
# Copyright (c) 2017
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
"""Tests for yardstick/api/server.py"""
from __future__ import absolute_import

import mock
import os
import socket
import unittest
import tempfile

from oslo_serialization import jsonutils

from yardstick.common import constants as consts


class APITestCase(unittest.TestCase):
    """Tests for the YardStick API server"""
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        consts.SQLITE = 'sqlite:///{}'.format(self.db_path)

        # server calls gethostbyname which takes 4 seconds, and we should mock
        # it anyway
        self.socket_mock = mock.patch.dict("sys.modules", {"socket": mock.MagicMock(
            **{"gethostbyname.return_value": "127.0.0.1",
               "gethostname.return_value": "localhost"})})
        self.socket_mock.start()
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
        self.socket_mock.stop()

    def _post(self, url, data):
        headers = {'Content-Type': 'application/json'}
        resp = self.app.post(url, data=jsonutils.dumps(data), headers=headers)
        return jsonutils.loads(resp.data)

    def _get(self, url):
        resp = self.app.get(url)
        return jsonutils.loads(resp.data)
