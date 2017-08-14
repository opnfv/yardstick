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

from __future__ import absolute_import
import unittest
from contextlib import contextmanager

import mock

STL_MOCKS = {
    'stl': mock.MagicMock(),
    'stl.trex_stl_lib': mock.MagicMock(),
    'stl.trex_stl_lib.base64': mock.MagicMock(),
    'stl.trex_stl_lib.binascii': mock.MagicMock(),
    'stl.trex_stl_lib.collections': mock.MagicMock(),
    'stl.trex_stl_lib.copy': mock.MagicMock(),
    'stl.trex_stl_lib.datetime': mock.MagicMock(),
    'stl.trex_stl_lib.functools': mock.MagicMock(),
    'stl.trex_stl_lib.imp': mock.MagicMock(),
    'stl.trex_stl_lib.inspect': mock.MagicMock(),
    'stl.trex_stl_lib.json': mock.MagicMock(),
    'stl.trex_stl_lib.linecache': mock.MagicMock(),
    'stl.trex_stl_lib.math': mock.MagicMock(),
    'stl.trex_stl_lib.os': mock.MagicMock(),
    'stl.trex_stl_lib.platform': mock.MagicMock(),
    'stl.trex_stl_lib.pprint': mock.MagicMock(),
    'stl.trex_stl_lib.random': mock.MagicMock(),
    'stl.trex_stl_lib.re': mock.MagicMock(),
    'stl.trex_stl_lib.scapy': mock.MagicMock(),
    'stl.trex_stl_lib.socket': mock.MagicMock(),
    'stl.trex_stl_lib.string': mock.MagicMock(),
    'stl.trex_stl_lib.struct': mock.MagicMock(),
    'stl.trex_stl_lib.sys': mock.MagicMock(),
    'stl.trex_stl_lib.threading': mock.MagicMock(),
    'stl.trex_stl_lib.time': mock.MagicMock(),
    'stl.trex_stl_lib.traceback': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_async_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_exceptions': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_ext': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_jsonrpc_client': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_interface': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_packet_builder_scapy': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_port': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_stats': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_streams': mock.MagicMock(),
    'stl.trex_stl_lib.trex_stl_types': mock.MagicMock(),
    'stl.trex_stl_lib.types': mock.MagicMock(),
    'stl.trex_stl_lib.utils': mock.MagicMock(),
    'stl.trex_stl_lib.utils.argparse': mock.MagicMock(),
    'stl.trex_stl_lib.utils.collections': mock.MagicMock(),
    'stl.trex_stl_lib.utils.common': mock.MagicMock(),
    'stl.trex_stl_lib.utils.json': mock.MagicMock(),
    'stl.trex_stl_lib.utils.os': mock.MagicMock(),
    'stl.trex_stl_lib.utils.parsing_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.pwd': mock.MagicMock(),
    'stl.trex_stl_lib.utils.random': mock.MagicMock(),
    'stl.trex_stl_lib.utils.re': mock.MagicMock(),
    'stl.trex_stl_lib.utils.string': mock.MagicMock(),
    'stl.trex_stl_lib.utils.sys': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_opts': mock.MagicMock(),
    'stl.trex_stl_lib.utils.text_tables': mock.MagicMock(),
    'stl.trex_stl_lib.utils.texttable': mock.MagicMock(),
    'stl.trex_stl_lib.warnings': mock.MagicMock(),
    'stl.trex_stl_lib.yaml': mock.MagicMock(),
    'stl.trex_stl_lib.zlib': mock.MagicMock(),
    'stl.trex_stl_lib.zmq': mock.MagicMock(),
}

STLClient = mock.MagicMock()
stl_patch = mock.patch.dict("sys.modules", STL_MOCKS)
stl_patch.start()

if stl_patch:
    from yardstick.benchmark.runners.search import SearchRunner
    from yardstick.benchmark.runners.search import SearchRunnerHelper


class TestSearchRunnerHelper(unittest.TestCase):

    def test___call__(self):
        cls = mock.MagicMock()
        aborted = mock.MagicMock()
        scenario_cfg = {
            'runner': {},
        }

        benchmark = cls()
        method = getattr(benchmark, 'my_method')
        helper = SearchRunnerHelper(cls, 'my_method', scenario_cfg, {}, aborted)

        with helper.get_benchmark_instance():
            helper()

        self.assertEqual(method.call_count, 1)

    def test___call___error(self):
        cls = mock.MagicMock()
        aborted = mock.MagicMock()
        scenario_cfg = {
            'runner': {},
        }

        helper = SearchRunnerHelper(cls, 'my_method', scenario_cfg, {}, aborted)

        with self.assertRaises(RuntimeError):
            helper()

    @mock.patch('yardstick.benchmark.runners.search.time')
    def test_is_not_done(self, mock_time):
        cls = mock.MagicMock()
        aborted = mock.MagicMock()
        scenario_cfg = {
            'runner': {},
        }

        mock_time.time.side_effect = range(1000)

        helper = SearchRunnerHelper(cls, 'my_method', scenario_cfg, {}, aborted)

        index = -1
        for index in helper.is_not_done():
            if index >= 10:
                break

        self.assertGreaterEqual(index, 10)

    @mock.patch('yardstick.benchmark.runners.search.time')
    def test_is_not_done_immediate_stop(self, mock_time):
        cls = mock.MagicMock()
        aborted = mock.MagicMock()
        scenario_cfg = {
            'runner': {
                'run_step': '',
            },
        }

        helper = SearchRunnerHelper(cls, 'my_method', scenario_cfg, {}, aborted)

        index = -1
        for index in helper.is_not_done():
            if index >= 10:
                break

        self.assertEqual(index, -1)

class TestSearchRunner(unittest.TestCase):

    def test__worker_run_once(self):
        def update(*args):
            args[-1].update(data)

        data = {
            'key1': {
                'inner1': 'value1',
                'done': 0,
            },
            'key2': {
                'done': None,
            },
        }

        runner = SearchRunner({})
        runner.worker_helper = mock.MagicMock(side_effect=update)

        self.assertFalse(runner._worker_run_once('sequence 1'))

    def test__worker_run_once_done(self):
        def update(*args):
            args[-1].update(data)

        data = {
            'key1': {
                'inner1': 'value1',
                'done': 0,
            },
            'key2': {
                'done': None,
            },
            'key3': {
                'done': True,
            },
            'key4': [],
            'key5': 'value5',
        }

        runner = SearchRunner({})
        runner.worker_helper = mock.MagicMock(side_effect=update)

        self.assertTrue(runner._worker_run_once('sequence 1'))

    def test__worker_run_once_assertion_error_assert(self):
        runner = SearchRunner({})
        runner.sla_action = 'assert'
        runner.worker_helper = mock.MagicMock(side_effect=AssertionError)

        with self.assertRaises(AssertionError):
            runner._worker_run_once('sequence 1')

    def test__worker_run_once_assertion_error_monitor(self):
        runner = SearchRunner({})
        runner.sla_action = 'monitor'
        runner.worker_helper = mock.MagicMock(side_effect=AssertionError)

        self.assertFalse(runner._worker_run_once('sequence 1'))

    def test__worker_run_once_non_assertion_error_none(self):
        runner = SearchRunner({})
        runner.worker_helper = mock.MagicMock(side_effect=RuntimeError)

        self.assertTrue(runner._worker_run_once('sequence 1'))

    def test__worker_run_once_non_assertion_error(self):
        runner = SearchRunner({})
        runner.sla_action = 'monitor'
        runner.worker_helper = mock.MagicMock(side_effect=RuntimeError)

        self.assertFalse(runner._worker_run_once('sequence 1'))

    def test__worker_run(self):
        cls = mock.MagicMock()
        scenario_cfg = {
            'runner': {'interval': 0, 'timeout': 1},
        }

        runner = SearchRunner({})
        runner._worker_run_once = mock.MagicMock(side_effect=[0, 0, 1])

        runner._worker_run(cls, 'my_method', scenario_cfg, {})

    def test__worker_run_immediate_stop(self):
        cls = mock.MagicMock()
        scenario_cfg = {
            'runner': {
                'run_step': '',
            },
        }

        runner = SearchRunner({})
        runner._worker_run(cls, 'my_method', scenario_cfg, {})

    @mock.patch('yardstick.benchmark.runners.search.multiprocessing')
    def test__run_benchmark(self, mock_multi_process):
        cls = mock.MagicMock()
        scenario_cfg = {
            'runner': {},
        }

        runner = SearchRunner({})
        runner._run_benchmark(cls, 'my_method', scenario_cfg, {})
        self.assertEqual(mock_multi_process.Process.call_count, 1)
