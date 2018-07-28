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
#

import mock
import unittest

from yardstick.tests import STL_MOCKS
from yardstick.network_services.vnf_generic.vnf import tg_landslide

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.network_services.vnf_generic.vnf.tg_landslide import \
        LandslideResourceHelper, LandslideTclClient, \
        LsTclHandler
    from yardstick.common.exceptions import LandslideTclException


EXAMPLE_URL = 'http://example.com/'


class TestLandslideTclClient(unittest.TestCase):
    def setUp(self):
        self.mock_tcl_handler = mock.MagicMock(spec=LsTclHandler)
        self.ls_res_helper = mock.MagicMock(spec=LandslideResourceHelper)

    def test___init__(self, *args):
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        self.assertIsNone(ls_tcl_client._url)
        self.assertIsNone(ls_tcl_client._user)
        self.assertIsNone(ls_tcl_client._library_id)
        self.assertIsNone(ls_tcl_client._basic_library_id)
        self.assertEqual(ls_tcl_client.ts_ids, set())
        self.assertIsInstance(ls_tcl_client._tc_types, set)
        self.assertIsNotNone(ls_tcl_client._tc_types)

    def test_connect_login_success(self, *args):
        lib_id = '123'
        exec_responses = ['java0x2', lib_id, lib_id]
        auth = ('user', 'password')
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        # First execute call returns a login handle
        # Second one represents library id returned by _get_library_id()
        self.mock_tcl_handler.execute.side_effect = exec_responses
        ls_tcl_client.connect(EXAMPLE_URL, auth)
        self.assertEqual(ls_tcl_client._library_id, lib_id)
        self.assertEqual(ls_tcl_client._basic_library_id, lib_id)
        self.assertEqual(ls_tcl_client._url, EXAMPLE_URL)
        self.assertEqual(ls_tcl_client._user, auth[0])
        self.assertEqual(self.mock_tcl_handler.execute.call_count,
                         len(exec_responses))

    def test_connect_login_failed(self, *args):
        exec_responses = ['Login failed']
        auth = ('user', 'password')
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        # First execute call returns a login handle
        # Second one represents library id returned by _get_library_id()
        self.mock_tcl_handler.execute.side_effect = exec_responses
        self.assertRaises(LandslideTclException, ls_tcl_client.connect,
                          EXAMPLE_URL, auth)
        self.assertIsNone(ls_tcl_client._library_id)
        self.assertIsNone(ls_tcl_client._basic_library_id)
        self.assertIsNone(ls_tcl_client._url)
        self.assertIsNone(ls_tcl_client._user)
        self.assertEqual(self.mock_tcl_handler.execute.call_count,
                         len(exec_responses))

    def test_disconnect(self, *args):
        ls_tcl_client = LandslideTclClient(self.mock_tcl_handler,
                                           self.ls_res_helper)
        ls_tcl_client.disconnect()
        self.assertEqual(self.mock_tcl_handler.execute.call_count, 1)
        self.assertIsNone(ls_tcl_client._url)
        self.assertIsNone(ls_tcl_client._user)
        self.assertIsNone(ls_tcl_client._library_id)
        self.assertIsNone(ls_tcl_client._basic_library_id)


class TestLsTclHandler(unittest.TestCase):

    def setUp(self):
        self.mock_lsapi = mock.patch.object(tg_landslide, 'LsApi')
        self.mock_lsapi.start()

        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.mock_lsapi.stop()

    def test___init__(self, *args):
        self.ls_tcl_handler = LsTclHandler()
        self.assertEquals(self.ls_tcl_handler.tcl_cmds, {})
        self.ls_tcl_handler._ls.tcl.assert_called_once()

    def test_execute(self, *args):
        self.ls_tcl_handler = LsTclHandler()
        self.ls_tcl_handler.execute('command')
        self.assertIn('command', self.ls_tcl_handler.tcl_cmds)
