##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import time
import uuid

import mock
from oslo_config import cfg
import oslo_messaging
import subprocess

from yardstick.benchmark.runners import base as runner_base
from yardstick.benchmark.runners import iteration
from yardstick.common import messaging
from yardstick.common.messaging import payloads
from yardstick.tests.unit import base as ut_base


class ActionTestCase(ut_base.BaseUnitTestCase):

    def setUp(self):
        self._mock_log = mock.patch.object(runner_base.log, 'error')
        self.mock_log = self._mock_log.start()
        self.addCleanup(self._stop_mocks)

    def _stop_mocks(self):
        self._mock_log.stop()

    @mock.patch.object(subprocess, 'check_output')
    def test__execute_shell_command(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(-1, '')
        self.assertEqual(runner_base._execute_shell_command("")[0], -1)

    @mock.patch.object(subprocess, 'check_output')
    def test__single_action(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(-1, '')
        runner_base._single_action(0, 'echo', mock.Mock())

    @mock.patch.object(subprocess, 'check_output')
    def test__periodic_action(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.CalledProcessError(-1, '')
        runner_base._periodic_action(0, 'echo', mock.Mock())


class RunnerTestCase(ut_base.BaseUnitTestCase):

    def setUp(self):
        config = {
            'output_config': {
                'DEFAULT': {
                    'dispatcher': 'file'
                }
            }
        }
        self.runner = iteration.IterationRunner(config)

    @mock.patch("yardstick.benchmark.runners.iteration.multiprocessing")
    def test_get_output(self, *args):
        self.runner.output_queue.put({'case': 'opnfv_yardstick_tc002'})
        self.runner.output_queue.put({'criteria': 'PASS'})

        idle_result = {
            'case': 'opnfv_yardstick_tc002',
            'criteria': 'PASS'
        }

        for _ in range(1000):
            time.sleep(0.01)
            if not self.runner.output_queue.empty():
                break
        actual_result = self.runner.get_output()
        self.assertEqual(idle_result, actual_result)

    @mock.patch("yardstick.benchmark.runners.iteration.multiprocessing")
    def test_get_result(self, *args):
        self.runner.result_queue.put({'case': 'opnfv_yardstick_tc002'})
        self.runner.result_queue.put({'criteria': 'PASS'})

        idle_result = [
            {'case': 'opnfv_yardstick_tc002'},
            {'criteria': 'PASS'}
        ]

        for _ in range(1000):
            time.sleep(0.01)
            if not self.runner.result_queue.empty():
                break
        actual_result = self.runner.get_result()
        self.assertEqual(idle_result, actual_result)

    def test__run_benchmark(self):
        runner = runner_base.Runner(mock.Mock())

        with self.assertRaises(NotImplementedError):
            runner._run_benchmark(mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock())


class RunnerProducerTestCase(ut_base.BaseUnitTestCase):

    @mock.patch.object(oslo_messaging, 'Target', return_value='rpc_target')
    @mock.patch.object(oslo_messaging, 'RPCClient')
    @mock.patch.object(oslo_messaging, 'get_rpc_transport',
                       return_value='rpc_transport')
    @mock.patch.object(cfg, 'CONF')
    def test__init(self, mock_config, mock_transport, mock_rpcclient,
                   mock_target):
        _id = uuid.uuid1().int
        runner_producer = runner_base.RunnerProducer(_id)
        mock_transport.assert_called_once_with(
            mock_config, url='rabbit://yardstick:yardstick@localhost:5672/')
        mock_target.assert_called_once_with(topic=messaging.TOPIC_RUNNER,
                                            fanout=True,
                                            server=messaging.SERVER)
        mock_rpcclient.assert_called_once_with('rpc_transport', 'rpc_target')
        self.assertEqual(_id, runner_producer._id)
        self.assertEqual(messaging.TOPIC_RUNNER, runner_producer._topic)

    @mock.patch.object(oslo_messaging, 'Target', return_value='rpc_target')
    @mock.patch.object(oslo_messaging, 'RPCClient')
    @mock.patch.object(oslo_messaging, 'get_rpc_transport',
                       return_value='rpc_transport')
    @mock.patch.object(payloads, 'RunnerPayload', return_value='runner_pload')
    def test_start_iteration(self, mock_runner_payload, *args):
        runner_producer = runner_base.RunnerProducer(uuid.uuid1().int)
        with mock.patch.object(runner_producer,
                               'send_message') as mock_message:
            runner_producer.start_iteration(version=10)

        mock_message.assert_called_once_with(
            messaging.RUNNER_METHOD_START_ITERATION, 'runner_pload')
        mock_runner_payload.assert_called_once_with(version=10, data={})

    @mock.patch.object(oslo_messaging, 'Target', return_value='rpc_target')
    @mock.patch.object(oslo_messaging, 'RPCClient')
    @mock.patch.object(oslo_messaging, 'get_rpc_transport',
                       return_value='rpc_transport')
    @mock.patch.object(payloads, 'RunnerPayload', return_value='runner_pload')
    def test_stop_iteration(self, mock_runner_payload, *args):
        runner_producer = runner_base.RunnerProducer(uuid.uuid1().int)
        with mock.patch.object(runner_producer,
                               'send_message') as mock_message:
            runner_producer.stop_iteration(version=15)

        mock_message.assert_called_once_with(
            messaging.RUNNER_METHOD_STOP_ITERATION, 'runner_pload')
        mock_runner_payload.assert_called_once_with(version=15, data={})
