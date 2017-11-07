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
import unittest

import mock

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
