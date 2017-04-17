import unittest
import mock

from yardstick.benchmark.scenarios.lib.migrate import Migrate
from yardstick.benchmark.scenarios.lib.migrate import PingThread

BASE = 'yardstick.benchmark.scenarios.lib.migrate'


class MigrateTestCase(unittest.TestCase):

    @mock.patch('{}.PingThread'.format(BASE))
    @mock.patch('{}.Migrate._get_current_host_name'.format(BASE))
    @mock.patch('{}.Migrate._get_migrate_time'.format(BASE))
    @mock.patch('{}.Migrate._do_migrate'.format(BASE))
    @mock.patch('{}.Migrate._do_ping_task'.format(BASE))
    @mock.patch('{}.Migrate._ping_until_connected'.format(BASE))
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_migrate_with_server_ip(self,
                                    mock_get_nova_client,
                                    mock_ping_until_connected,
                                    mock_do_ping_task,
                                    mock_do_migrate,
                                    mock_get_migrate_time,
                                    mock_get_current_host_name,
                                    mock_ping_thread):
        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }
        mock_get_migrate_time.return_value = 10
        mock_get_current_host_name.return_value = 'host5'
        mock_ping_thread().delay = 0.48
        obj = Migrate(scenario_cfg, {})
        result = obj.run({})
        self.assertEqual(result['migrate_time'], 10)

    @mock.patch('{}.PingThread'.format(BASE))
    @mock.patch('{}.Migrate._get_current_host_name'.format(BASE))
    @mock.patch('{}.Migrate._get_migrate_time'.format(BASE))
    @mock.patch('{}.Migrate._do_migrate'.format(BASE))
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_migrate_without_server_ip(self,
                                       mock_get_nova_client,
                                       mock_do_migrate,
                                       mock_get_migrate_time,
                                       mock_get_current_host_name,
                                       mock_ping_thread):
        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5'
            },
            'output': 'status migrate_time'
        }
        mock_get_migrate_time.return_value = 10
        mock_get_current_host_name.return_value = 'host4'
        mock_ping_thread().delay = 0.48
        obj = Migrate(scenario_cfg, {})
        result = obj.run({})
        self.assertEqual(result['status'], 1)

    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_get_migrate_time_success(self, mock_get_nova_client):
        class A(object):
            def __init__(self, status):
                self.status = status

        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }
        mock_get_nova_client().servers.get.side_effect = [A('migrating'), A('active')]
        obj = Migrate(scenario_cfg, {})
        result = obj._get_migrate_time('1')
        self.assertTrue(result < 1)

    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_get_migrate_time_error(self, mock_get_nova_client):
        class A(object):
            def __init__(self, status):
                self.status = status

        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }
        mock_get_nova_client().servers.get.side_effect = [A('migrating'), A('error')]
        obj = Migrate(scenario_cfg, {})
        try:
            obj._get_migrate_time('1')
        except Exception as e:
            self.assertIsInstance(e, RuntimeError)

    @mock.patch('subprocess.Popen')
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_do_migrate(self, mock_get_nova_client, mock_popen):
        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }

        obj = Migrate(scenario_cfg, {})
        obj._do_migrate('1', 'host5')
        self.assertTrue(mock_popen.called)

    @mock.patch('ping.do_one')
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_ping_until_connected(self, mock_get_nova_client, mock_do_one):
        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }
        mock_do_one.return_value = 0.01

        obj = Migrate(scenario_cfg, {})
        obj._ping_until_connected('127.0.0.1')
        self.assertTrue(mock_do_one.called)

    @mock.patch('{}.PingThread.start'.format(BASE))
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_do_ping_task(self, mock_get_nova_client, mock_start):
        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }

        obj = Migrate(scenario_cfg, {})
        obj._do_ping_task('127.0.0.1')
        self.assertTrue(mock_start.called)

    @mock.patch('{}.change_obj_to_dict'.format(BASE))
    @mock.patch('yardstick.common.openstack_utils.get_nova_client')
    def test_get_current_host_name(self, mock_get_nova_client, mock_change_obj_to_dict):
        scenario_cfg = {
            'options': {
                'server_id': '1',
                'host': 'host5',
                'server_ip': '127.0.0.1'
            },
            'output': 'status migrate_time downtime'
        }
        mock_get_nova_client().servers.get.return_value = ''
        mock_change_obj_to_dict.return_value = {'OS-EXT-SRV-ATTR:host': 'host5'}

        obj = Migrate(scenario_cfg, {})
        result = obj._get_current_host_name('1')
        self.assertEqual(result, 'host5')


class PingThreadTestCase(unittest.TestCase):

    @mock.patch('ping.do_one')
    def test_run(self, mock_do_one):
        mock_do_one.side_effect = [0.1, 0.1, 0]
        obj = PingThread('127.0.0.1')
        obj.start()
        obj.flag = False


def main():
    unittest.main()


if __name__ == '__main__':
    main()
