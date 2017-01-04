##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import unittest
import mock
import uuid

from yardstick.cmd.commands.env import EnvCommand


class EnvCommandTestCase(unittest.TestCase):

    @mock.patch('yardstick.cmd.commands.env.EnvCommand._start_async_task')
    @mock.patch('yardstick.cmd.commands.env.EnvCommand._check_status')
    def test_do_influxdb(self, check_status_mock, start_async_task_mock):
        env = EnvCommand()
        env.do_influxdb({})
        self.assertTrue(start_async_task_mock.called)
        self.assertTrue(check_status_mock.called)

    @mock.patch('yardstick.cmd.commands.env.EnvCommand._start_async_task')
    @mock.patch('yardstick.cmd.commands.env.EnvCommand._check_status')
    def test_do_grafana(self, check_status_mock, start_async_task_mock):
        env = EnvCommand()
        env.do_grafana({})
        self.assertTrue(start_async_task_mock.called)
        self.assertTrue(check_status_mock.called)

    @mock.patch('yardstick.cmd.commands.env.EnvCommand._start_async_task')
    @mock.patch('yardstick.cmd.commands.env.EnvCommand._check_status')
    def test_do_prepare(self, check_status_mock, start_async_task_mock):
        env = EnvCommand()
        env.do_prepare({})
        self.assertTrue(start_async_task_mock.called)
        self.assertTrue(check_status_mock.called)

    @mock.patch('yardstick.cmd.commands.env.HttpClient.post')
    def test_start_async_task(self, post_mock):
        data = {'action': 'createGrafanaContainer'}
        EnvCommand()._start_async_task(data)
        self.assertTrue(post_mock.called)

    @mock.patch('yardstick.cmd.commands.env.HttpClient.get')
    @mock.patch('yardstick.cmd.commands.env.time')
    def test_check_status(self, time_mock, get_mock):
        task_id = str(uuid.uuid4())
        get_mock.return_value = {'status': 1, 'result': 'error'}
        EnvCommand()._check_status(task_id, 'hello world')
        self.assertTrue(get_mock.called)

    def test_print_status(self):
        try:
            EnvCommand()._print_status('hello', 'word')
        except Exception as e:
            self.assertIsInstance(e, IndexError)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
