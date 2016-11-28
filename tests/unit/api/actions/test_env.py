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


def main():
    unittest.main()


if __name__ == '__main__':
    main()
