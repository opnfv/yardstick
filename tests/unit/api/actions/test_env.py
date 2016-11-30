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

from api.actions import env


class CreateInfluxDBContainerTestCase(unittest.TestCase):

    @mock.patch('api.actions.env._create_influxdb_container')
    def test_create_influxdb_container(self, mock_create_container):
        env.createInfluxDBContainer({})
        mock_create_container.assert_called_with()


class CreateInfluxdbContainerTestCase(unittest.TestCase):

    @mock.patch('api.actions.env.Client')
    def test_create_influxdb_container(self, mock_influx_client):
        env._create_influxdb_container()
        self.assertFalse(mock_influx_client()._create_container.called)


class ConfigInfluxdbTestCase(unittest.TestCase):

    @mock.patch('api.actions.env.influx.get_data_db_client')
    def test_config_influxdb(self, mock_influx_client):
        env._config_influxdb()
        mock_influx_client.assert_called_with()


class ConfigOutputFile(unittest.TestCase):

    def test_config_output_file(self):
        pass


def main():
    unittest.main()


if __name__ == '__main__':
    main()
