# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import multiprocessing
import unittest
import socket
import sys
import time

from yardstick.common import utils


class ImportModulesFromPackageTestCase(unittest.TestCase):

    def test_import_package(self):
        module_name = 'yardstick.tests.functional.common.fake_module'
        library_name = 'fake_library'
        class_name = 'FakeClassToBeImported'
        self.assertNotIn(module_name, sys.modules)

        utils.import_modules_from_package(module_name)
        self.assertIn(module_name, sys.modules)
        module_obj = sys.modules[module_name]
        library_obj = getattr(module_obj, library_name)
        class_obj = getattr(library_obj, class_name)
        self.assertEqual(class_name, class_obj().__class__.__name__)


class SendSocketCommandTestCase(unittest.TestCase):

    @staticmethod
    def _run_socket_server(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', port))
        sock.listen(1)
        conn = None
        while not conn:
            conn, _ = sock.accept()
        sock.close()

    @staticmethod
    def _terminate_server(socket_server):
        # Wait until the socket server closes the open port.
        time.sleep(1)
        if socket_server and socket_server.is_alive():
            socket_server.terminate()

    def test_send_command(self):
        port = 47001

        socket_server = multiprocessing.Process(
            name='run_socket_server',
            target=SendSocketCommandTestCase._run_socket_server,
            args=(port, )).start()

        self.addCleanup(self._terminate_server, socket_server)

        # Wait until the socket is open.
        time.sleep(0.5)
        self.assertEqual(
            0, utils.send_socket_command('localhost', port, 'test_command'))
