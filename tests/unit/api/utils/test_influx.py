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
import datetime

from api.utils import influx


class GetDataDbClientTestCase(unittest.TestCase):

    @mock.patch('api.utils.influx.ConfigParser')
    def test_get_data_db_client_dispatcher_not_influxdb(self, mock_parser):
        mock_parser.ConfigParser().get.return_value = 'file'
        try:
            influx.get_data_db_client()
        except Exception as e:
            self.assertIsInstance(e, RuntimeError)


class GetIpTestCase(unittest.TestCase):

    def test_get_url(self):
        url = 'http://localhost:8086/hello'
        output = influx._get_ip(url)

        result = 'localhost'
        self.assertEqual(result, output)


class WriteDataTestCase(unittest.TestCase):

    @mock.patch('api.utils.influx.get_data_db_client')
    def test_write_data(self, mock_get_client):
        measurement = 'tasklist'
        field = {'status': 1}
        timestamp = datetime.datetime.now()
        tags = {'task_id': str(uuid.uuid4())}

        influx._write_data(measurement, field, timestamp, tags)
        mock_get_client.assert_called_with()


class WriteDataTasklistTestCase(unittest.TestCase):

    @mock.patch('api.utils.influx._write_data')
    def test_write_data_tasklist(self, mock_write_data):
        task_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now()
        status = 1
        influx.write_data_tasklist(task_id, timestamp, status)

        field = {'status': status, 'error': ''}
        tags = {'task_id': task_id}
        mock_write_data.assert_called_with('tasklist', field, timestamp, tags)


class QueryTestCase(unittest.TestCase):

    @mock.patch('api.utils.influx.ConfigParser')
    def test_query_dispatcher_not_influxdb(self, mock_parser):
        mock_parser.ConfigParser().get.return_value = 'file'
        try:
            sql = 'select * form tasklist'
            influx.query(sql)
        except Exception as e:
            self.assertIsInstance(e, RuntimeError)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
