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

import mock
import unittest

from oslo_utils import encodeutils

from yardstick.common import exceptions
from yardstick.common import process


class ProcessTestcase(unittest.TestCase):
    def test_check_if_procces_failed_None(self):
        p = mock.MagicMock(**{"exitcode": None, "name": "debug"})
        process.check_if_process_failed(p)

    def test_check_if_procces_failed_0(self):
        p = mock.MagicMock(**{"exitcode": 0, "name": "debug"})
        process.check_if_process_failed(p)

    def test_check_if_procces_failed_1(self):
        p = mock.MagicMock(**{"exitcode": 1, "name": "debug"})
        with self.assertRaises(RuntimeError):
            process.check_if_process_failed(p)


@mock.patch("yardstick.common.process.multiprocessing")
class TerminateChildrenTestcase(unittest.TestCase):
    def test_some_children(self, mock_multiprocessing):
        p1 = mock.MagicMock()
        p2 = mock.MagicMock()
        mock_multiprocessing.active_children.return_value = [p1, p2]
        process.terminate_children()

    def test_no_children(self, mock_multiprocessing):
        mock_multiprocessing.active_children.return_value = []
        process.terminate_children()


class ExecuteTestCase(unittest.TestCase):

    RET_CODE_OK = 0
    RET_CODE_WRONG = 1

    def setUp(self):
        self._mock_create_process = mock.patch.object(process,
                                                      'create_process')
        self.mock_create_process = self._mock_create_process.start()
        self.obj = mock.Mock()
        self.cmd = mock.Mock()
        self.obj.communicate = mock.Mock()
        self.stdout = 'std out'
        self.stderr = 'std err'
        self.obj.communicate.return_value = (self.stdout, self.stderr)
        self.mock_create_process.return_value = (self.obj, self.cmd)
        self.input_cmd = 'input cmd'
        self.additional_env = mock.Mock()

    def test_execute_with_input(self):
        process_input = 'process input'
        self.obj.returncode = self.RET_CODE_OK
        out = process.execute(self.input_cmd, process_input=process_input,
                              additional_env=self.additional_env)
        self.obj.communicate.assert_called_once_with(
            encodeutils.to_utf8(process_input))
        self.mock_create_process.assert_called_once_with(
            self.input_cmd, run_as_root=False,
            additional_env=self.additional_env)
        self.assertEqual(self.stdout, out)

    def test_execute_no_input(self):
        self.obj.returncode = self.RET_CODE_OK
        out = process.execute(self.input_cmd,
                              additional_env=self.additional_env)
        self.obj.communicate.assert_called_once_with(None)
        self.mock_create_process.assert_called_once_with(
            self.input_cmd, run_as_root=False,
            additional_env=self.additional_env)
        self.assertEqual(self.stdout, out)

    def test_execute_exception(self):
        self.obj.returncode = self.RET_CODE_WRONG
        self.assertRaises(exceptions.ProcessExecutionError, process.execute,
                          self.input_cmd, additional_env=self.additional_env)
        self.obj.communicate.assert_called_once_with(None)

    def test_execute_with_extra_code(self):
        self.obj.returncode = self.RET_CODE_WRONG
        out = process.execute(self.input_cmd,
                              additional_env=self.additional_env,
                              extra_ok_codes=[self.RET_CODE_WRONG])
        self.obj.communicate.assert_called_once_with(None)
        self.mock_create_process.assert_called_once_with(
            self.input_cmd, run_as_root=False,
            additional_env=self.additional_env)
        self.assertEqual(self.stdout, out)

    def test_execute_exception_no_check(self):
        self.obj.returncode = self.RET_CODE_WRONG
        out = process.execute(self.input_cmd,
                              additional_env=self.additional_env,
                              check_exit_code=False)
        self.obj.communicate.assert_called_once_with(None)
        self.mock_create_process.assert_called_once_with(
            self.input_cmd, run_as_root=False,
            additional_env=self.additional_env)
        self.assertEqual(self.stdout, out)


class CreateProcessTestCase(unittest.TestCase):

    @mock.patch.object(process, 'subprocess_popen')
    def test_process_string_command(self, mock_subprocess_popen):
        cmd = 'command'
        obj = mock.Mock()
        mock_subprocess_popen.return_value = obj
        out1, out2 = process.create_process(cmd)
        self.assertEqual(obj, out1)
        self.assertEqual([cmd], out2)

    @mock.patch.object(process, 'subprocess_popen')
    def test_process_list_command(self, mock_subprocess_popen):
        cmd = ['command']
        obj = mock.Mock()
        mock_subprocess_popen.return_value = obj
        out1, out2 = process.create_process(cmd)
        self.assertEqual(obj, out1)
        self.assertEqual(cmd, out2)

    @mock.patch.object(process, 'subprocess_popen')
    def test_process_with_env(self, mock_subprocess_popen):
        cmd = ['command']
        obj = mock.Mock()
        additional_env = {'var1': 'value1'}
        mock_subprocess_popen.return_value = obj
        out1, out2 = process.create_process(cmd, additional_env=additional_env)
        self.assertEqual(obj, out1)
        self.assertEqual(['env', 'var1=value1'] + cmd, out2)
