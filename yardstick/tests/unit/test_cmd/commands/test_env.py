##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import os
import sys

import mock
import uuid

from yardstick.cmd.commands import env
from yardstick.tests.unit import base


class EnvCommandTestCase(base.BaseUnitTestCase):

    @mock.patch.object(env.EnvCommand, '_start_async_task')
    @mock.patch.object(env.EnvCommand, '_check_status')
    def test_do_influxdb(self, check_status_mock, start_async_task_mock):
        _env = env.EnvCommand()
        _env.do_influxdb({})
        start_async_task_mock.assert_called_once()
        check_status_mock.assert_called_once()

    @mock.patch.object(env.EnvCommand, '_start_async_task')
    @mock.patch.object(env.EnvCommand, '_check_status')
    def test_do_grafana(self, check_status_mock, start_async_task_mock):
        _env = env.EnvCommand()
        _env.do_grafana({})
        start_async_task_mock.assert_called_once()
        check_status_mock.assert_called_once()

    @mock.patch.object(env.EnvCommand, '_start_async_task')
    @mock.patch.object(env.EnvCommand, '_check_status')
    def test_do_prepare(self, check_status_mock, start_async_task_mock):
        _env = env.EnvCommand()
        _env.do_prepare({})
        start_async_task_mock.assert_called_once()
        check_status_mock.assert_called_once()

    @mock.patch.object(env.HttpClient, 'post')
    def test_start_async_task(self, post_mock):
        data = {'action': 'create_grafana'}
        env.EnvCommand()._start_async_task(data)
        post_mock.assert_called_once()

    @mock.patch.object(env.HttpClient, 'get')
    @mock.patch.object(env.EnvCommand, '_print_status')
    def test_check_status(self, mock_print, mock_get):
        task_id = str(uuid.uuid4())
        mock_get.return_value = {'status': 2, 'result': 'error'}
        self.assertEqual(
            2, env.EnvCommand()._check_status(task_id, 'hello world'))
        self.assertEqual(2, mock_print.call_count)

    @mock.patch.object(sys, 'stdout')
    @mock.patch.object(os, 'popen')
    def test_print_status(self, mock_popen, mock_stdout):
        mock_popen_obj = mock.Mock()
        mock_popen_obj.read.return_value = ''
        mock_popen.return_value = mock_popen_obj
        env.EnvCommand()._print_status('hello', 'word')
        mock_stdout.write.assert_not_called()
        mock_stdout.flush.assert_not_called()
