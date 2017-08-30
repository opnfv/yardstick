# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this file is a modified copy of
# rally/tests/unit/common/test_sshutils.py

from __future__ import absolute_import
import os
import socket
import unittest
from io import StringIO

import mock
from oslo_utils import encodeutils

from yardstick import ssh
from yardstick.ssh import SSHError
from yardstick.ssh import SSH
from yardstick.ssh import AutoConnectSSH


class FakeParamikoException(Exception):
    pass


class SSHTestCase(unittest.TestCase):
    """Test all small SSH methods."""

    def setUp(self):
        super(SSHTestCase, self).setUp()
        self.test_client = ssh.SSH("root", "example.net")

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    def test_construct(self, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "pkey"
        test_ssh = ssh.SSH("root", "example.net", port=33, pkey="key",
                           key_filename="kf", password="secret")
        mock_ssh__get_pkey.assert_called_once_with("key")
        self.assertEqual("root", test_ssh.user)
        self.assertEqual("example.net", test_ssh.host)
        self.assertEqual(33, test_ssh.port)
        self.assertEqual("pkey", test_ssh.pkey)
        self.assertEqual("kf", test_ssh.key_filename)
        self.assertEqual("secret", test_ssh.password)

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    def test_ssh_from_node(self, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "pkey"
        node = {
            "user": "root", "ip": "example.net", "ssh_port": 33,
            "key_filename": "kf", "password": "secret"
        }
        test_ssh = ssh.SSH.from_node(node)
        self.assertEqual("root", test_ssh.user)
        self.assertEqual("example.net", test_ssh.host)
        self.assertEqual(33, test_ssh.port)
        self.assertEqual("kf", test_ssh.key_filename)
        self.assertEqual("secret", test_ssh.password)

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    def test_ssh_from_node_password_default(self, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "pkey"
        node = {
            "user": "root", "ip": "example.net", "ssh_port": 33,
            "key_filename": "kf"
        }
        test_ssh = ssh.SSH.from_node(node)
        self.assertEqual("root", test_ssh.user)
        self.assertEqual("example.net", test_ssh.host)
        self.assertEqual(33, test_ssh.port)
        self.assertEqual("kf", test_ssh.key_filename)
        self.assertIsNone(test_ssh.password)

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    def test_ssh_from_node_ssh_port_default(self, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "pkey"
        node = {
            "user": "root", "ip": "example.net",
            "key_filename": "kf", "password": "secret"
        }
        test_ssh = ssh.SSH.from_node(node)
        self.assertEqual("root", test_ssh.user)
        self.assertEqual("example.net", test_ssh.host)
        self.assertEqual(ssh.SSH.SSH_PORT, test_ssh.port)
        self.assertEqual("kf", test_ssh.key_filename)
        self.assertEqual("secret", test_ssh.password)

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    def test_ssh_from_node_key_filename_default(self, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "pkey"
        node = {
            "user": "root", "ip": "example.net", "ssh_port": 33,
            "password": "secret"
        }
        test_ssh = ssh.SSH.from_node(node)
        self.assertEqual("root", test_ssh.user)
        self.assertEqual("example.net", test_ssh.host)
        self.assertEqual(33, test_ssh.port)
        self.assertIsNone(test_ssh.key_filename)
        self.assertEqual("secret", test_ssh.password)

    def test_construct_default(self):
        self.assertEqual("root", self.test_client.user)
        self.assertEqual("example.net", self.test_client.host)
        self.assertEqual(22, self.test_client.port)
        self.assertIsNone(self.test_client.pkey)
        self.assertIsNone(self.test_client.key_filename)
        self.assertIsNone(self.test_client.password)

    @mock.patch("yardstick.ssh.paramiko")
    def test__get_pkey_invalid(self, mock_paramiko):
        mock_paramiko.SSHException = FakeParamikoException
        rsa = mock_paramiko.rsakey.RSAKey
        dss = mock_paramiko.dsskey.DSSKey
        rsa.from_private_key.side_effect = mock_paramiko.SSHException
        dss.from_private_key.side_effect = mock_paramiko.SSHException
        self.assertRaises(ssh.SSHError, self.test_client._get_pkey, "key")

    @mock.patch("yardstick.ssh.six.moves.StringIO")
    @mock.patch("yardstick.ssh.paramiko")
    def test__get_pkey_dss(self, mock_paramiko, mock_string_io):
        mock_paramiko.SSHException = FakeParamikoException
        mock_string_io.return_value = "string_key"
        mock_paramiko.dsskey.DSSKey.from_private_key.return_value = "dss_key"
        rsa = mock_paramiko.rsakey.RSAKey
        rsa.from_private_key.side_effect = mock_paramiko.SSHException
        key = self.test_client._get_pkey("key")
        dss_calls = mock_paramiko.dsskey.DSSKey.from_private_key.mock_calls
        self.assertEqual([mock.call("string_key")], dss_calls)
        self.assertEqual(key, "dss_key")
        mock_string_io.assert_called_once_with("key")

    @mock.patch("yardstick.ssh.six.moves.StringIO")
    @mock.patch("yardstick.ssh.paramiko")
    def test__get_pkey_rsa(self, mock_paramiko, mock_string_io):
        mock_paramiko.SSHException = FakeParamikoException
        mock_string_io.return_value = "string_key"
        mock_paramiko.rsakey.RSAKey.from_private_key.return_value = "rsa_key"
        dss = mock_paramiko.dsskey.DSSKey
        dss.from_private_key.side_effect = mock_paramiko.SSHException
        key = self.test_client._get_pkey("key")
        rsa_calls = mock_paramiko.rsakey.RSAKey.from_private_key.mock_calls
        self.assertEqual([mock.call("string_key")], rsa_calls)
        self.assertEqual(key, "rsa_key")
        mock_string_io.assert_called_once_with("key")

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    @mock.patch("yardstick.ssh.paramiko")
    def test__get_client(self, mock_paramiko, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "key"
        fake_client = mock.Mock()
        mock_paramiko.SSHClient.return_value = fake_client
        mock_paramiko.AutoAddPolicy.return_value = "autoadd"

        test_ssh = ssh.SSH("admin", "example.net", pkey="key")
        client = test_ssh._get_client()

        self.assertEqual(fake_client, client)
        client_calls = [
            mock.call.set_missing_host_key_policy("autoadd"),
            mock.call.connect("example.net", username="admin",
                              port=22, pkey="key", key_filename=None,
                              password=None,
                              allow_agent=False, look_for_keys=False,
                              timeout=1),
        ]
        self.assertEqual(client_calls, client.mock_calls)

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    @mock.patch("yardstick.ssh.paramiko")
    def test__get_client_with_exception(self, mock_paramiko, mock_ssh__get_pkey):
        class MyError(Exception):
            pass

        mock_ssh__get_pkey.return_value = "pkey"
        fake_client = mock.Mock()
        fake_client.connect.side_effect = MyError
        fake_client.set_missing_host_key_policy.return_value = None
        mock_paramiko.SSHClient.return_value = fake_client
        mock_paramiko.AutoAddPolicy.return_value = "autoadd"

        test_ssh = ssh.SSH("admin", "example.net", pkey="key")

        with self.assertRaises(SSHError) as raised:
            test_ssh._get_client()

        self.assertEqual(mock_paramiko.SSHClient.call_count, 1)
        self.assertEqual(mock_paramiko.AutoAddPolicy.call_count, 1)
        self.assertEqual(fake_client.set_missing_host_key_policy.call_count, 1)
        self.assertEqual(fake_client.connect.call_count, 1)
        exc_str = str(raised.exception)
        self.assertIn('raised during connect', exc_str)
        self.assertIn('MyError', exc_str)

    @mock.patch("yardstick.ssh.SSH._get_pkey")
    @mock.patch("yardstick.ssh.paramiko")
    def test_copy(self, mock_paramiko, mock_ssh__get_pkey):
        mock_ssh__get_pkey.return_value = "pkey"
        fake_client = mock.Mock()
        fake_client.connect.side_effect = IOError
        mock_paramiko.SSHClient.return_value = fake_client
        mock_paramiko.AutoAddPolicy.return_value = "autoadd"

        test_ssh = ssh.SSH("admin", "example.net", pkey="key")
        result = test_ssh.copy()
        self.assertIsNot(test_ssh, result)

    def test_close(self):
        with mock.patch.object(self.test_client, "_client") as m_client:
            self.test_client.close()
        m_client.close.assert_called_once_with()
        self.assertFalse(self.test_client._client)

    @mock.patch("yardstick.ssh.six.moves.StringIO")
    def test_execute(self, mock_string_io):
        mock_string_io.side_effect = stdio = [mock.Mock(), mock.Mock()]
        stdio[0].read.return_value = "stdout fake data"
        stdio[1].read.return_value = "stderr fake data"
        with mock.patch.object(self.test_client, "run", return_value=0)\
                as mock_run:
            status, stdout, stderr = self.test_client.execute(
                "cmd",
                stdin="fake_stdin",
                timeout=43)
        mock_run.assert_called_once_with(
            "cmd", stdin="fake_stdin", stdout=stdio[0],
            stderr=stdio[1], timeout=43, raise_on_error=False)
        self.assertEqual(0, status)
        self.assertEqual("stdout fake data", stdout)
        self.assertEqual("stderr fake data", stderr)

    @mock.patch("yardstick.ssh.time")
    def test_wait_timeout(self, mock_time):
        mock_time.time.side_effect = [1, 50, 150]
        self.test_client.execute = mock.Mock(side_effect=[ssh.SSHError,
                                                          ssh.SSHError,
                                                          0])
        self.assertRaises(ssh.SSHTimeout, self.test_client.wait)
        self.assertEqual([mock.call("uname")] * 2,
                         self.test_client.execute.mock_calls)

    @mock.patch("yardstick.ssh.time")
    def test_wait(self, mock_time):
        mock_time.time.side_effect = [1, 50, 100]
        self.test_client.execute = mock.Mock(side_effect=[ssh.SSHError,
                                                          ssh.SSHError,
                                                          0])
        self.test_client.wait()
        self.assertEqual([mock.call("uname")] * 3,
                         self.test_client.execute.mock_calls)

    @mock.patch("yardstick.ssh.paramiko")
    def test_send_command(self, mock_paramiko):
        paramiko_sshclient = self.test_client._get_client()
        with mock.patch.object(paramiko_sshclient, "exec_command") \
                as mock_paramiko_exec_command:
            self.test_client.send_command('cmd')
        mock_paramiko_exec_command.assert_called_once_with('cmd',
                                                           get_pty=True)


class SSHRunTestCase(unittest.TestCase):
    """Test SSH.run method in different aspects.

    Also tested method "execute".
    """

    def setUp(self):
        super(SSHRunTestCase, self).setUp()

        self.fake_client = mock.Mock()
        self.fake_session = mock.Mock()
        self.fake_transport = mock.Mock()

        self.fake_transport.open_session.return_value = self.fake_session
        self.fake_client.get_transport.return_value = self.fake_transport

        self.fake_session.recv_ready.return_value = False
        self.fake_session.recv_stderr_ready.return_value = False
        self.fake_session.send_ready.return_value = False
        self.fake_session.exit_status_ready.return_value = True
        self.fake_session.recv_exit_status.return_value = 0

        self.test_client = ssh.SSH("admin", "example.net")
        self.test_client._get_client = mock.Mock(return_value=self.fake_client)

    @mock.patch("yardstick.ssh.select")
    def test_execute(self, mock_select):
        mock_select.select.return_value = ([], [], [])
        self.fake_session.recv_ready.side_effect = [1, 0, 0]
        self.fake_session.recv_stderr_ready.side_effect = [1, 0]
        self.fake_session.recv.return_value = "ok"
        self.fake_session.recv_stderr.return_value = "error"
        self.fake_session.exit_status_ready.return_value = 1
        self.fake_session.recv_exit_status.return_value = 127
        self.assertEqual((127, "ok", "error"), self.test_client.execute("cmd"))
        self.fake_session.exec_command.assert_called_once_with("cmd")

    @mock.patch("yardstick.ssh.select")
    def test_execute_args(self, mock_select):
        mock_select.select.return_value = ([], [], [])
        self.fake_session.recv_ready.side_effect = [1, 0, 0]
        self.fake_session.recv_stderr_ready.side_effect = [1, 0]
        self.fake_session.recv.return_value = "ok"
        self.fake_session.recv_stderr.return_value = "error"
        self.fake_session.exit_status_ready.return_value = 1
        self.fake_session.recv_exit_status.return_value = 127

        result = self.test_client.execute("cmd arg1 'arg2 with space'")
        self.assertEqual((127, "ok", "error"), result)
        self.fake_session.exec_command.assert_called_once_with(
            "cmd arg1 'arg2 with space'")

    @mock.patch("yardstick.ssh.select")
    def test_run(self, mock_select):
        mock_select.select.return_value = ([], [], [])
        self.assertEqual(0, self.test_client.run("cmd"))

    @mock.patch("yardstick.ssh.select")
    def test_run_nonzero_status(self, mock_select):
        mock_select.select.return_value = ([], [], [])
        self.fake_session.recv_exit_status.return_value = 1
        self.assertRaises(ssh.SSHError, self.test_client.run, "cmd")
        self.assertEqual(1, self.test_client.run("cmd", raise_on_error=False))

    @mock.patch("yardstick.ssh.select")
    def test_run_stdout(self, mock_select):
        mock_select.select.return_value = ([], [], [])
        self.fake_session.recv_ready.side_effect = [True, True, False]
        self.fake_session.recv.side_effect = ["ok1", "ok2"]
        stdout = mock.Mock()
        self.test_client.run("cmd", stdout=stdout)
        self.assertEqual([mock.call("ok1"), mock.call("ok2")],
                         stdout.write.mock_calls)

    @mock.patch("yardstick.ssh.select")
    def test_run_stderr(self, mock_select):
        mock_select.select.return_value = ([], [], [])
        self.fake_session.recv_stderr_ready.side_effect = [True, False]
        self.fake_session.recv_stderr.return_value = "error"
        stderr = mock.Mock()
        self.test_client.run("cmd", stderr=stderr)
        stderr.write.assert_called_once_with("error")

    @mock.patch("yardstick.ssh.select")
    def test_run_stdin(self, mock_select):
        """Test run method with stdin.

        Third send call was called with "e2" because only 3 bytes was sent
        by second call. So remainig 2 bytes of "line2" was sent by third call.
        """
        mock_select.select.return_value = ([], [], [])
        self.fake_session.exit_status_ready.side_effect = [0, 0, 0, True]
        self.fake_session.send_ready.return_value = True
        self.fake_session.send.side_effect = [5, 3, 2]
        fake_stdin = mock.Mock()
        fake_stdin.read.side_effect = ["line1", "line2", ""]
        fake_stdin.closed = False

        def close():
            fake_stdin.closed = True
        fake_stdin.close = mock.Mock(side_effect=close)
        self.test_client.run("cmd", stdin=fake_stdin)
        call = mock.call
        send_calls = [call(encodeutils.safe_encode("line1", "utf-8")),
                      call(encodeutils.safe_encode("line2", "utf-8")),
                      call(encodeutils.safe_encode("e2", "utf-8"))]
        self.assertEqual(send_calls, self.fake_session.send.mock_calls)

    @mock.patch("yardstick.ssh.select")
    def test_run_stdin_keep_open(self, mock_select):
        """Test run method with stdin.

        Third send call was called with "e2" because only 3 bytes was sent
        by second call. So remainig 2 bytes of "line2" was sent by third call.
        """
        mock_select.select.return_value = ([], [], [])
        self.fake_session.exit_status_ready.side_effect = [0, 0, 0, True]
        self.fake_session.send_ready.return_value = True
        self.fake_session.send.side_effect = len
        fake_stdin = StringIO(u"line1\nline2\n")
        self.test_client.run("cmd", stdin=fake_stdin, keep_stdin_open=True)
        call = mock.call
        send_calls = [call(encodeutils.safe_encode("line1\nline2\n", "utf-8"))]
        self.assertEqual(send_calls, self.fake_session.send.mock_calls)

    @mock.patch("yardstick.ssh.select")
    def test_run_select_error(self, mock_select):
        self.fake_session.exit_status_ready.return_value = False
        mock_select.select.return_value = ([], [], [True])
        self.assertRaises(ssh.SSHError, self.test_client.run, "cmd")

    @mock.patch("yardstick.ssh.time")
    @mock.patch("yardstick.ssh.select")
    def test_run_timemout(self, mock_select, mock_time):
        mock_time.time.side_effect = [1, 3700]
        mock_select.select.return_value = ([], [], [])
        self.fake_session.exit_status_ready.return_value = False
        self.assertRaises(ssh.SSHTimeout, self.test_client.run, "cmd")

    @mock.patch("yardstick.ssh.open", create=True)
    def test__put_file_shell(self, mock_open):
        with mock.patch.object(self.test_client, "run") as run_mock:
            self.test_client._put_file_shell("localfile", "remotefile", 0o42)
            run_mock.assert_called_once_with(
                'cat > "remotefile"&& chmod -- 042 "remotefile"',
                stdin=mock_open.return_value.__enter__.return_value)

    @mock.patch("yardstick.ssh.open", create=True)
    def test__put_file_shell_space(self, mock_open):
        with mock.patch.object(self.test_client, "run") as run_mock:
            self.test_client._put_file_shell("localfile",
                                             "filename with space", 0o42)
            run_mock.assert_called_once_with(
                'cat > "filename with space"&& chmod -- 042 "filename with '
                'space"',
                stdin=mock_open.return_value.__enter__.return_value)

    @mock.patch("yardstick.ssh.open", create=True)
    def test__put_file_shell_tilde(self, mock_open):
        with mock.patch.object(self.test_client, "run") as run_mock:
            self.test_client._put_file_shell("localfile", "~/remotefile", 0o42)
            run_mock.assert_called_once_with(
                'cat > ~/"remotefile"&& chmod -- 042 ~/"remotefile"',
                stdin=mock_open.return_value.__enter__.return_value)

    @mock.patch("yardstick.ssh.open", create=True)
    def test__put_file_shell_tilde_spaces(self, mock_open):
        with mock.patch.object(self.test_client, "run") as run_mock:
            self.test_client._put_file_shell("localfile", "~/file with space",
                                             0o42)
            run_mock.assert_called_once_with(
                'cat > ~/"file with space"&& chmod -- 042 ~/"file with space"',
                stdin=mock_open.return_value.__enter__.return_value)

    @mock.patch("yardstick.ssh.os.stat")
    def test__put_file_sftp(self, mock_stat):
        sftp = self.fake_client.open_sftp.return_value = mock.MagicMock()
        sftp.__enter__.return_value = sftp

        mock_stat.return_value = os.stat_result([0o753] + [0] * 9)

        self.test_client._put_file_sftp("localfile", "remotefile")

        sftp.put.assert_called_once_with("localfile", "remotefile")
        mock_stat.assert_any_call("localfile")
        sftp.chmod.assert_any_call("remotefile", 0o753)
        sftp.__exit__.assert_called_once_with(None, None, None)

    def test__put_file_sftp_mode(self):
        sftp = self.fake_client.open_sftp.return_value = mock.MagicMock()
        sftp.__enter__.return_value = sftp

        self.test_client._put_file_sftp("localfile", "remotefile", mode=0o753)

        sftp.put.assert_called_once_with("localfile", "remotefile")
        sftp.chmod.assert_called_once_with("remotefile", 0o753)
        sftp.__exit__.assert_called_once_with(None, None, None)

    def test_put_file_SSHException(self):
        exc = ssh.paramiko.SSHException
        self.test_client._put_file_sftp = mock.Mock(side_effect=exc())
        self.test_client._put_file_shell = mock.Mock()

        self.test_client.put_file("foo", "bar", 42)
        self.test_client._put_file_sftp.assert_called_once_with("foo", "bar",
                                                                mode=42)
        self.test_client._put_file_shell.assert_called_once_with("foo", "bar",
                                                                 mode=42)

    def test_put_file_socket_error(self):
        exc = socket.error
        self.test_client._put_file_sftp = mock.Mock(side_effect=exc())
        self.test_client._put_file_shell = mock.Mock()

        self.test_client.put_file("foo", "bar", 42)
        self.test_client._put_file_sftp.assert_called_once_with("foo", "bar",
                                                                mode=42)
        self.test_client._put_file_shell.assert_called_once_with("foo", "bar",
                                                                 mode=42)

    @mock.patch("yardstick.ssh.os.stat")
    def test_put_file_obj_with_mode(self, mock_stat):
        sftp = self.fake_client.open_sftp.return_value = mock.MagicMock()
        sftp.__enter__.return_value = sftp

        mock_stat.return_value = os.stat_result([0o753] + [0] * 9)

        self.test_client.put_file_obj("localfile", "remotefile", 'my_mode')

        sftp.__enter__.assert_called_once()
        sftp.putfo.assert_called_once_with("localfile", "remotefile")
        sftp.chmod.assert_called_once_with("remotefile", 'my_mode')
        sftp.__exit__.assert_called_once_with(None, None, None)


class TestAutoConnectSSH(unittest.TestCase):

    def test__connect_with_wait(self):
        auto_connect_ssh = AutoConnectSSH('user1', 'host1', wait=True)
        auto_connect_ssh._get_client = mock.Mock()
        auto_connect_ssh.wait = mock_wait = mock.Mock()

        auto_connect_ssh._connect()
        self.assertEqual(mock_wait.call_count, 1)

    def test__make_dict(self):
        auto_connect_ssh = AutoConnectSSH('user1', 'host1')

        expected = {
            'user': 'user1',
            'host': 'host1',
            'port': SSH.SSH_PORT,
            'pkey': None,
            'key_filename': None,
            'password': None,
            'name': None,
            'wait': False,
        }
        result = auto_connect_ssh._make_dict()
        self.assertDictEqual(result, expected)

    def test_get_class(self):
        auto_connect_ssh = AutoConnectSSH('user1', 'host1')

        self.assertEqual(auto_connect_ssh.get_class(), AutoConnectSSH)

    @mock.patch('yardstick.ssh.SCPClient')
    def test_put(self, mock_scp_client_type):
        auto_connect_ssh = AutoConnectSSH('user1', 'host1')
        auto_connect_ssh._client = mock.Mock()

        auto_connect_ssh.put('a', 'z')
        with mock_scp_client_type() as mock_scp_client:
            self.assertEqual(mock_scp_client.put.call_count, 1)

    def test_put_file(self):
        auto_connect_ssh = AutoConnectSSH('user1', 'host1')
        auto_connect_ssh._client = mock.Mock()
        auto_connect_ssh._put_file_sftp = mock_put_sftp = mock.Mock()

        auto_connect_ssh.put_file('a', 'b')
        self.assertEqual(mock_put_sftp.call_count, 1)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
