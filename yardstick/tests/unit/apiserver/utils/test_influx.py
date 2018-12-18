##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
# Copyright (c) 2019 Intel Corporation.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from influxdb import client as influxdb_client
import mock
from six.moves import configparser

from api.utils import influx
from yardstick.common import constants
from yardstick.common import exceptions
from yardstick import dispatcher
from yardstick.tests.unit import base


class GetDataDbClientTestCase(base.BaseUnitTestCase):

    @mock.patch.object(influx, '_get_influxdb_client',
                       return_value='fake_client')
    @mock.patch.object(influx.ConfigParser, 'ConfigParser')
    def test_get_data_db_client(self, mock_parser, mock_get_client):
        _mock_parser = mock.Mock()
        mock_parser.return_value = _mock_parser

        self.assertEqual('fake_client', influx.get_data_db_client())
        _mock_parser.read.assert_called_once_with(constants.CONF_FILE)
        mock_get_client.assert_called_once_with(_mock_parser, None)

    @mock.patch.object(influx.logger, 'error')
    @mock.patch.object(influx, '_get_influxdb_client',
                       return_value='fake_client')
    @mock.patch.object(influx.ConfigParser, 'ConfigParser')
    def test_get_data_db_client_parsing_error(
            self, mock_parser, mock_get_client, *args):
        _mock_parser = mock.Mock()
        mock_parser.return_value = _mock_parser
        mock_parser.NoOptionError = configparser.NoOptionError
        mock_get_client.side_effect = configparser.NoOptionError('option',
                                                                 'section')
        with self.assertRaises(configparser.NoOptionError):
            influx.get_data_db_client()

        _mock_parser.read.assert_called_once_with(constants.CONF_FILE)
        mock_get_client.assert_called_once_with(_mock_parser, None)


class GetIpTestCase(base.BaseUnitTestCase):

    def test_get_url(self):
        url = 'http://localhost:8086/hello'
        output = influx._get_ip(url)

        result = 'localhost'
        self.assertEqual(result, output)


class GetInfluxdbTestCase(base.BaseUnitTestCase):

    @mock.patch.object(influxdb_client, 'InfluxDBClient',
                       return_value='idb_client')
    @mock.patch.object(influx, '_get_ip', return_value='fake_ip')
    def test_get_influxdb_client(self, mock_get_ip, mock_client):
        mock_parser = mock.Mock()
        mock_parser.get.side_effect = [dispatcher.INFLUXDB, 'target', 'user',
                                       'pass', 'db_name']

        self.assertEqual('idb_client',
                         influx._get_influxdb_client(mock_parser))
        mock_client.assert_called_once_with('fake_ip', constants.INFLUXDB_PORT,
                                            'user', 'pass', 'db_name')
        mock_get_ip.assert_called_once_with('target')
        mock_parser.get.assert_has_calls([
            mock.call('DEFAULT', 'dispatcher'),
            mock.call('dispatcher_influxdb', 'target'),
            mock.call('dispatcher_influxdb', 'username'),
            mock.call('dispatcher_influxdb', 'password'),
            mock.call('dispatcher_influxdb', 'db_name')])

    def test_get_influxdb_client_no_influxdb_client(self):
        mock_parser = mock.Mock()
        mock_parser.get.return_value = dispatcher.FILE

        with self.assertRaises(exceptions.InfluxDBConfigurationMissing):
            influx._get_influxdb_client(mock_parser)
        mock_parser.get.assert_called_once_with('DEFAULT', 'dispatcher')
