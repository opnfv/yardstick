##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
from six.moves import configparser

from api.utils import influx
from yardstick.common import constants
from yardstick.common import exceptions
from yardstick import dispatcher
from yardstick.tests.unit import base


class GetDataDbClientTestCase(base.BaseUnitTestCase):

    @mock.patch.object(influx, '_get_client', return_value='fake_client')
    @mock.patch.object(influx.ConfigParser, 'ConfigParser')
    def test_get_data_db_client(self, mock_parser, mock_get_client):
        _mock_parser = mock.Mock()
        mock_parser.return_value = _mock_parser
        _mock_parser.get.return_value = dispatcher.INFLUXDB

        self.assertEqual('fake_client', influx.get_data_db_client())
        _mock_parser.read.assert_called_once_with(constants.CONF_FILE)
        _mock_parser.get.assert_called_once_with('DEFAULT', 'dispatcher')
        mock_get_client.assert_called_once_with(_mock_parser)

    @mock.patch.object(influx.ConfigParser, 'ConfigParser')
    def test_get_data_db_client_dispatcher_not_influxdb(self, mock_parser):
        _mock_parser = mock.Mock()
        mock_parser.return_value = _mock_parser
        _mock_parser.get.return_value = dispatcher.FILE
        with self.assertRaises(exceptions.InfluxDBConfigurationMissing):
            influx.get_data_db_client()

        _mock_parser.read.assert_called_once_with(constants.CONF_FILE)
        _mock_parser.get.assert_called_once_with('DEFAULT', 'dispatcher')

    @mock.patch.object(influx, '_get_client', return_value='fake_client')
    @mock.patch.object(influx.ConfigParser, 'ConfigParser')
    def test_get_data_db_client_parsing_error(self, mock_parser,
                                              mock_get_client):
        _mock_parser = mock.Mock()
        mock_parser.return_value = _mock_parser
        _mock_parser.get.return_value = dispatcher.INFLUXDB
        mock_parser.NoOptionError = configparser.NoOptionError
        mock_get_client.side_effect = configparser.NoOptionError('option', 'section')
        with self.assertRaises(configparser.NoOptionError):
            influx.get_data_db_client()

        _mock_parser.read.assert_called_once_with(constants.CONF_FILE)
        _mock_parser.get.assert_called_once_with('DEFAULT', 'dispatcher')
        mock_get_client.assert_called_once_with(_mock_parser)


class GetIpTestCase(base.BaseUnitTestCase):

    def test_get_url(self):
        url = 'http://localhost:8086/hello'
        output = influx._get_ip(url)

        result = 'localhost'
        self.assertEqual(result, output)
