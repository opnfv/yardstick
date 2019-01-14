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

# yardstick comment: this is a modified copy of rally/rally/common/sshutils.py

"""High level ssh library.

Usage examples:

Execute command and get output:

    ssh = sshclient.SSH("root", "example.com", port=33)
    status, stdout, stderr = ssh.execute("ps ax")
    if status:
        raise Exception("Command failed with non-zero status.")
    print(stdout.splitlines())

Execute command with huge output:

    class PseudoFile(io.RawIOBase):
        def write(chunk):
            if "error" in chunk:
                email_admin(chunk)

    ssh = SSH("root", "example.com")
    with PseudoFile() as p:
        ssh.run("tail -f /var/log/syslog", stdout=p, timeout=False)

Execute local script on remote side:

    ssh = sshclient.SSH("user", "example.com")

    with open("~/myscript.sh", "r") as stdin_file:
        status, out, err = ssh.execute('/bin/sh -s "arg1" "arg2"',
                                       stdin=stdin_file)

Upload file:

    ssh = SSH("user", "example.com")
    # use rb for binary files
    with open("/store/file.gz", "rb") as stdin_file:
        ssh.run("cat > ~/upload/file.gz", stdin=stdin_file)

Eventlet:

    eventlet.monkey_patch(select=True, time=True)
    or
    eventlet.monkey_patch()
    or
    sshclient = eventlet.import_patched("yardstick.ssh")

"""
import io
import logging
import os
import re
import select
import socket
import time

import paramiko
from chainmap import ChainMap
from oslo_utils import encodeutils
from scp import SCPClient
import six

from yardstick.common import exceptions
from yardstick.common.utils import try_int, NON_NONE_DEFAULT, make_dict_from_map
from yardstick.network_services.utils import provision_tool


def convert_key_to_str(key):
    if not isinstance(key, (paramiko.RSAKey, paramiko.DSSKey)):
        return key
    k = io.StringIO()
    key.write_private_key(k)
    return k.getvalue()


# class SSHError(Exception):
#     pass
#
#
# class SSHTimeout(SSHError):
#     pass


class SSH(object):
    """Represent ssh connection."""

    SSH_PORT = paramiko.config.SSH_PORT
    DEFAULT_WAIT_TIMEOUT = 120

    @staticmethod
    def gen_keys(key_filename, bit_count=2048):
        rsa_key = paramiko.RSAKey.generate(bits=bit_count, progress_func=None)
        rsa_key.write_private_key_file(key_filename)
        print("Writing %s ..." % key_filename)
        with open('.'.join([key_filename, "pub"]), "w") as pubkey_file:
            pubkey_file.write(rsa_key.get_name())
            pubkey_file.write(' ')
            pubkey_file.write(rsa_key.get_base64())
            pubkey_file.write('\n')

    @staticmethod
    def get_class():
        # must return static class name, anything else refers to the calling class
        # i.e. the subclass, not the superclass
        return SSH

    @classmethod
    def get_arg_key_map(cls):
        return {
            'user': ('user', NON_NONE_DEFAULT),
            'host': ('ip', NON_NONE_DEFAULT),
            'port': ('ssh_port', cls.SSH_PORT),
            'pkey': ('pkey', None),
            'key_filename': ('key_filename', None),
            'password': ('password', None),
            'name': ('name', None),
        }

    def __init__(self, user, host, port=None, pkey=None,
                 key_filename=None, password=None, name=None):
        """Initialize SSH client.

        :param user: ssh username
        :param host: hostname or ip address of remote ssh server
        :param port: remote ssh port
        :param pkey: RSA or DSS private key string or file object
        :param key_filename: private key filename
        :param password: password
        """
        self.name = name
        if name:
            self.log = logging.getLogger(__name__ + '.' + self.name)
        else:
            self.log = logging.getLogger(__name__)

        self.wait_timeout = self.DEFAULT_WAIT_TIMEOUT
        self.user = user
        self.host = host
        # everybody wants to debug this in the caller, do it here instead
        self.log.debug("user:%s host:%s", user, host)

        # we may get text port from YAML, convert to int
        self.port = try_int(port, self.SSH_PORT)
        self.pkey = self._get_pkey(pkey) if pkey else None
        self.password = password
        self.key_filename = key_filename
        self._client = False
        # paramiko loglevel debug will output ssh protocl debug
        # we don't ever really want that unless we are debugging paramiko
        # ssh issues
        if os.environ.get("PARAMIKO_DEBUG", "").lower() == "true":
            logging.getLogger("paramiko").setLevel(logging.DEBUG)
        else:
            logging.getLogger("paramiko").setLevel(logging.WARN)

    @classmethod
    def args_from_node(cls, node, overrides=None, defaults=None):
        if overrides is None:
            overrides = {}
        if defaults is None:
            defaults = {}

        params = ChainMap(overrides, node, defaults)
        return make_dict_from_map(params, cls.get_arg_key_map())

    @classmethod
    def from_node(cls, node, overrides=None, defaults=None):
        return cls(**cls.args_from_node(node, overrides, defaults))

    def _get_pkey(self, key):
        if isinstance(key, six.string_types):
            key = six.moves.StringIO(key)
        errors = []
        for key_class in (paramiko.rsakey.RSAKey, paramiko.dsskey.DSSKey):
            try:
                return key_class.from_private_key(key)
            except paramiko.SSHException as e:
                errors.append(e)
        raise exceptions.SSHError(error_msg='Invalid pkey: %s' % errors)

    @property
    def is_connected(self):
        return bool(self._client)

    def _get_client(self):
        if self.is_connected:
            return self._client
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(self.host, username=self.user,
                                 port=self.port, pkey=self.pkey,
                                 key_filename=self.key_filename,
                                 password=self.password,
                                 allow_agent=False, look_for_keys=False,
                                 timeout=1)
            return self._client
        except Exception as e:
            message = ("Exception %(exception_type)s was raised "
                       "during connect. Exception value is: %(exception)r" %
                       {"exception": e, "exception_type": type(e)})
            self._client = False
            raise exceptions.SSHError(error_msg=message)

    def _make_dict(self):
        return {
            'user': self.user,
            'host': self.host,
            'port': self.port,
            'pkey': self.pkey,
            'key_filename': self.key_filename,
            'password': self.password,
            'name': self.name,
        }

    def copy(self):
        return self.get_class()(**self._make_dict())

    def close(self):
        if self._client:
            self._client.close()
            self._client = False

    def run(self, cmd, stdin=None, stdout=None, stderr=None,
            raise_on_error=True, timeout=3600,
            keep_stdin_open=False, pty=False):
        """Execute specified command on the server.

        :param cmd:             Command to be executed.
        :type cmd:              str
        :param stdin:           Open file or string to pass to stdin.
        :param stdout:          Open file to connect to stdout.
        :param stderr:          Open file to connect to stderr.
        :param raise_on_error:  If False then exit code will be return. If True
                                then exception will be raized if non-zero code.
        :param timeout:         Timeout in seconds for command execution.
                                Default 1 hour. No timeout if set to 0.
        :param keep_stdin_open: don't close stdin on empty reads
        :type keep_stdin_open:  bool
        :param pty:             Request a pseudo terminal for this connection.
                                This allows passing control characters.
                                Default False.
        :type pty:              bool
        """

        client = self._get_client()

        if isinstance(stdin, six.string_types):
            stdin = six.moves.StringIO(stdin)

        return self._run(client, cmd, stdin=stdin, stdout=stdout,
                         stderr=stderr, raise_on_error=raise_on_error,
                         timeout=timeout,
                         keep_stdin_open=keep_stdin_open, pty=pty)

    def _run(self, client, cmd, stdin=None, stdout=None, stderr=None,
             raise_on_error=True, timeout=3600,
             keep_stdin_open=False, pty=False):

        transport = client.get_transport()
        session = transport.open_session()
        if pty:
            session.get_pty()
        session.exec_command(cmd)
        start_time = time.time()

        # encode on transmit, decode on receive
        data_to_send = encodeutils.safe_encode("", incoming='utf-8')
        stderr_data = None

        # If we have data to be sent to stdin then `select' should also
        # check for stdin availability.
        if stdin and not stdin.closed:
            writes = [session]
        else:
            writes = []

        while True:
            # Block until data can be read/write.
            e = select.select([session], writes, [session], 1)[2]

            if session.recv_ready():
                data = encodeutils.safe_decode(session.recv(4096), 'utf-8')
                self.log.debug("stdout: %r", data)
                if stdout is not None:
                    stdout.write(data)
                continue

            if session.recv_stderr_ready():
                stderr_data = encodeutils.safe_decode(
                    session.recv_stderr(4096), 'utf-8')
                self.log.debug("stderr: %r", stderr_data)
                if stderr is not None:
                    stderr.write(stderr_data)
                continue

            if session.send_ready():
                if stdin is not None and not stdin.closed:
                    if not data_to_send:
                        stdin_txt = stdin.read(4096)
                        if stdin_txt is None:
                            stdin_txt = ''
                        data_to_send = encodeutils.safe_encode(
                            stdin_txt, incoming='utf-8')
                        if not data_to_send:
                            # we may need to keep stdin open
                            if not keep_stdin_open:
                                stdin.close()
                                session.shutdown_write()
                                writes = []
                    if data_to_send:
                        sent_bytes = session.send(data_to_send)
                        # LOG.debug("sent: %s" % data_to_send[:sent_bytes])
                        data_to_send = data_to_send[sent_bytes:]

            if session.exit_status_ready():
                break

            if timeout and (time.time() - timeout) > start_time:
                message = ('Timeout executing command %(cmd)s on host %(host)s'
                           % {"cmd": cmd, "host": self.host})
                raise exceptions.SSHTimeout(error_msg=message)
            if e:
                raise exceptions.SSHError(error_msg='Socket error')

        exit_status = session.recv_exit_status()
        if exit_status != 0 and raise_on_error:
            fmt = "Command '%(cmd)s' failed with exit_status %(status)d."
            details = fmt % {"cmd": cmd, "status": exit_status}
            if stderr_data:
                details += " Last stderr data: '%s'." % stderr_data
            raise exceptions.SSHError(error_msg=details)
        return exit_status

    def execute(self, cmd, stdin=None, timeout=3600, raise_on_error=False):
        """Execute the specified command on the server.

        :param cmd: (str)             Command to be executed.
        :param stdin: (StringIO)      Open file to be sent on process stdin.
        :param timeout: (int)         Timeout for execution of the command.
        :param raise_on_error: (bool) If True, then an SSHError will be raised
                                      when non-zero exit code.

        :returns: tuple (exit_status, stdout, stderr)
        """
        stdout = six.moves.StringIO()
        stderr = six.moves.StringIO()

        exit_status = self.run(cmd, stderr=stderr,
                               stdout=stdout, stdin=stdin,
                               timeout=timeout, raise_on_error=raise_on_error)
        stdout.seek(0)
        stderr.seek(0)
        return exit_status, stdout.read(), stderr.read()

    def wait(self, timeout=None, interval=1):
        """Wait for the host will be available via ssh."""
        if timeout is None:
            timeout = self.wait_timeout

        end_time = time.time() + timeout
        while True:
            try:
                return self.execute("uname")
            except (socket.error, exceptions.SSHError) as e:
                self.log.debug("Ssh is still unavailable: %r", e)
                time.sleep(interval)
            if time.time() > end_time:
                raise exceptions.SSHTimeout(
                    error_msg='Timeout waiting for "%s"' % self.host)

    def put(self, files, remote_path=b'.', recursive=False):
        client = self._get_client()

        with SCPClient(client.get_transport()) as scp:
            scp.put(files, remote_path, recursive)

    def get(self, remote_path, local_path='/tmp/', recursive=True):
        client = self._get_client()

        with SCPClient(client.get_transport()) as scp:
            scp.get(remote_path, local_path, recursive)

    # keep shell running in the background, e.g. screen
    def send_command(self, command):
        client = self._get_client()
        client.exec_command(command, get_pty=True)

    def _put_file_sftp(self, localpath, remotepath, mode=None):
        client = self._get_client()

        with client.open_sftp() as sftp:
            sftp.put(localpath, remotepath)
            if mode is None:
                mode = 0o777 & os.stat(localpath).st_mode
            sftp.chmod(remotepath, mode)

    TILDE_EXPANSIONS_RE = re.compile("(^~[^/]*/)?(.*)")

    def _put_file_shell(self, localpath, remotepath, mode=None):
        # quote to stop wordpslit
        tilde, remotepath = self.TILDE_EXPANSIONS_RE.match(remotepath).groups()
        if not tilde:
            tilde = ''
        cmd = ['cat > %s"%s"' % (tilde, remotepath)]
        if mode is not None:
            # use -- so no options
            cmd.append('chmod -- 0%o %s"%s"' % (mode, tilde, remotepath))

        with open(localpath, "rb") as localfile:
            # only chmod on successful cat
            self.run("&& ".join(cmd), stdin=localfile)

    def put_file(self, localpath, remotepath, mode=None):
        """Copy specified local file to the server.

        :param localpath:   Local filename.
        :param remotepath:  Remote filename.
        :param mode:        Permissions to set after upload
        """
        try:
            self._put_file_sftp(localpath, remotepath, mode=mode)
        except (paramiko.SSHException, socket.error):
            self._put_file_shell(localpath, remotepath, mode=mode)

    def provision_tool(self, tool_path, tool_file=None):
        return provision_tool(self, tool_path, tool_file)

    def put_file_obj(self, file_obj, remotepath, mode=None):
        client = self._get_client()

        with client.open_sftp() as sftp:
            sftp.putfo(file_obj, remotepath)
            if mode is not None:
                sftp.chmod(remotepath, mode)

    def get_file_obj(self, remotepath, file_obj):
        client = self._get_client()

        with client.open_sftp() as sftp:
            sftp.getfo(remotepath, file_obj)

    def interactive_terminal_open(self, time_out=45):
        """Open interactive terminal on a SSH channel.

        :param time_out: Timeout in seconds.
        :returns: SSH channel with opened terminal.

        .. warning:: Interruptingcow is used here, and it uses
           signal(SIGALRM) to let the operating system interrupt program
           execution. This has the following limitations: Python signal
           handlers only apply to the main thread, so you cannot use this
           from other threads. You must not use this in a program that
           uses SIGALRM itself (this includes certain profilers)
        """
        chan = self._get_client().get_transport().open_session()
        chan.get_pty()
        chan.invoke_shell()
        chan.settimeout(int(time_out))
        chan.set_combine_stderr(True)

        buf = ''
        while not buf.endswith((":~# ", ":~$ ", "~]$ ", "~]# ")):
            try:
                chunk = chan.recv(10 * 1024 * 1024)
                if not chunk:
                    break
                buf += chunk
                if chan.exit_status_ready():
                    self.log.error('Channel exit status ready')
                    break
            except socket.timeout:
                raise exceptions.SSHTimeout(error_msg='Socket timeout: %s' % buf)
        return chan

    def interactive_terminal_exec_command(self, chan, cmd, prompt):
        """Execute command on interactive terminal.

        interactive_terminal_open() method has to be called first!

        :param chan: SSH channel with opened terminal.
        :param cmd: Command to be executed.
        :param prompt: Command prompt, sequence of characters used to
        indicate readiness to accept commands.
        :returns: Command output.

        .. warning:: Interruptingcow is used here, and it uses
           signal(SIGALRM) to let the operating system interrupt program
           execution. This has the following limitations: Python signal
           handlers only apply to the main thread, so you cannot use this
           from other threads. You must not use this in a program that
           uses SIGALRM itself (this includes certain profilers)
        """
        chan.sendall('{c}\n'.format(c=cmd))
        buf = ''
        while not buf.endswith(prompt):
            try:
                chunk = chan.recv(10 * 1024 * 1024)
                if not chunk:
                    break
                buf += chunk
                if chan.exit_status_ready():
                    self.log.error('Channel exit status ready')
                    break
            except socket.timeout:
                message = ("Socket timeout during execution of command: "
                           "%(cmd)s\nBuffer content:\n%(buf)s" % {"cmd": cmd,
                                                                  "buf": buf})
                raise exceptions.SSHTimeout(error_msg=message)
        tmp = buf.replace(cmd.replace('\n', ''), '')
        for item in prompt:
            tmp.replace(item, '')
        return tmp

    @staticmethod
    def interactive_terminal_close(chan):
        """Close interactive terminal SSH channel.

        :param: chan: SSH channel to be closed.
        """
        chan.close()


class AutoConnectSSH(SSH):

    @classmethod
    def get_arg_key_map(cls):
        arg_key_map = super(AutoConnectSSH, cls).get_arg_key_map()
        arg_key_map['wait'] = ('wait', True)
        return arg_key_map

    # always wait or we will get OpenStack SSH errors
    def __init__(self, user, host, port=None, pkey=None,
                 key_filename=None, password=None, name=None, wait=True):
        super(AutoConnectSSH, self).__init__(user, host, port, pkey, key_filename, password, name)
        if wait and wait is not True:
            self.wait_timeout = int(wait)

    def _make_dict(self):
        data = super(AutoConnectSSH, self)._make_dict()
        data.update({
            'wait': self.wait_timeout
        })
        return data

    def _connect(self):
        if not self.is_connected:
            interval = 1
            timeout = self.wait_timeout

            end_time = time.time() + timeout
            while True:
                try:
                    return self._get_client()
                except (socket.error, exceptions.SSHError) as e:
                    self.log.debug("Ssh is still unavailable: %r", e)
                    time.sleep(interval)
                if time.time() > end_time:
                    raise exceptions.SSHTimeout(
                        error_msg='Timeout waiting for "%s"' % self.host)

    def drop_connection(self):
        """ Don't close anything, just force creation of a new client """
        self._client = False

    def execute(self, cmd, stdin=None, timeout=3600, raise_on_error=False):
        self._connect()
        return super(AutoConnectSSH, self).execute(cmd, stdin, timeout,
                                                   raise_on_error)

    def run(self, cmd, stdin=None, stdout=None, stderr=None,
            raise_on_error=True, timeout=3600,
            keep_stdin_open=False, pty=False):
        self._connect()
        return super(AutoConnectSSH, self).run(cmd, stdin, stdout, stderr, raise_on_error,
                                               timeout, keep_stdin_open, pty)

    def put(self, files, remote_path=b'.', recursive=False):
        self._connect()
        return super(AutoConnectSSH, self).put(files, remote_path, recursive)

    def put_file(self, local_path, remote_path, mode=None):
        self._connect()
        return super(AutoConnectSSH, self).put_file(local_path, remote_path, mode)

    def put_file_obj(self, file_obj, remote_path, mode=None):
        self._connect()
        return super(AutoConnectSSH, self).put_file_obj(file_obj, remote_path, mode)

    def get_file_obj(self, remote_path, file_obj):
        self._connect()
        return super(AutoConnectSSH, self).get_file_obj(remote_path, file_obj)

    def provision_tool(self, tool_path, tool_file=None):
        self._connect()
        return super(AutoConnectSSH, self).provision_tool(tool_path, tool_file)

    @staticmethod
    def get_class():
        # must return static class name, anything else refers to the calling class
        # i.e. the subclass, not the superclass
        return AutoConnectSSH
