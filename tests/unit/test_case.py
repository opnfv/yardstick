#!/usr/bin/env python

# Copyright (c) 2017 Intel Corporation
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
#

# Unittest for yardstick.benchmark.contexts.standalone
import os
import mock

from contextlib import contextmanager
from unittest import TestCase

from yardstick import ssh

_LOCAL_OBJECT = object()


class MockError(BaseException):
    pass


class YardstickTestCase(TestCase):

    FILE_OBJ = __file__

    @staticmethod
    def mock_ssh(mock_ssh_type, spec=None, exec_result=_LOCAL_OBJECT, run_result=_LOCAL_OBJECT):
        if spec is None:
            spec = ssh.SSH

        if exec_result is _LOCAL_OBJECT:
            exec_result = 0, "", ""

        if run_result is _LOCAL_OBJECT:
            run_result = 0, "", ""

        ssh_mock = mock.Mock(autospec=spec)
        ssh_mock._get_client.return_value = mock.Mock()
        ssh_mock.execute.return_value = exec_result
        ssh_mock.run.return_value = run_result
        mock_ssh_type.from_node.return_value = ssh_mock
        return ssh_mock

    @classmethod
    def get_file_abspath(cls, filename):
        curr_path = os.path.dirname(os.path.abspath(cls.FILE_OBJ))
        file_path = os.path.join(curr_path, filename)
        return file_path

    @contextmanager
    def assertRaisesWithMessage(self, exc_class, message):
        try:
            yield
        except exc_class:
            pass
        else:
            raise self.fail(message)
