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

from api.utils import influx
from six.moves import configparser as ConfigParser


class GetDataDbClientTestCase(unittest.TestCase):

    @mock.patch('api.utils.influx.ConfigParser')
    def test_get_data_db_client_dispatcher_not_influxdb(self, mock_parser):
        mock_parser.ConfigParser().get.return_value = 'file'
        # reset exception to avoid
        # TypeError: catching classes that do not inherit from BaseException
        mock_parser.NoOptionError = ConfigParser.NoOptionError
        try:
            influx.get_data_db_client()
        except Exception as e:  # pylint: disable=broad-except
            self.assertIsInstance(e, RuntimeError)


class GetIpTestCase(unittest.TestCase):

    def test_get_url(self):
        url = 'http://localhost:8086/hello'
        output = influx._get_ip(url)

        result = 'localhost'
        self.assertEqual(result, output)


class QueryTestCase(unittest.TestCase):

    @mock.patch('api.utils.influx.ConfigParser')
    def test_query_dispatcher_not_influxdb(self, mock_parser):
        mock_parser.ConfigParser().get.return_value = 'file'
        # reset exception to avoid
        # TypeError: catching classes that do not inherit from BaseException
        mock_parser.NoOptionError = ConfigParser.NoOptionError
        try:
            sql = 'select * form tasklist'
            influx.query(sql)
        except Exception as e:  # pylint: disable=broad-except
            self.assertIsInstance(e, RuntimeError)
