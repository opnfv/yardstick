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
    print stdout.splitlines()

Execute command with huge output:

    class PseudoFile(object):
        def write(chunk):
            if "error" in chunk:
                email_admin(chunk)

    ssh = sshclient.SSH("root", "example.com")
    ssh.run("tail -f /var/log/syslog", stdout=PseudoFile(), timeout=False)

Execute local script on remote side:

    ssh = sshclient.SSH("user", "example.com")
    status, out, err = ssh.execute("/bin/sh -s arg1 arg2",
                                   stdin=open("~/myscript.sh", "r"))

Upload file:

    ssh = sshclient.SSH("user", "example.com")
    ssh.run("cat > ~/upload/file.gz", stdin=open("/store/file.gz", "rb"))

Eventlet:

    eventlet.monkey_patch(select=True, time=True)
    or
    eventlet.monkey_patch()
    or
    sshclient = eventlet.import_patched("opentstack.common.sshclient")

"""
import os
import select
import socket
import time

import logging
import paramiko
from scp import SCPClient
import six


DEFAULT_PORT = 22


class SSHError(Exception):
    pass


class SSHTimeout(SSHError):
    pass


class SSH(object):
    """Represent ssh connection."""

    def __init__(self, user, host, port=DEFAULT_PORT, pkey=None,
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

        self.user = user
        self.host = host
        # we may get text port from YAML, convert to int
        self.port = int(port)
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

    def _get_pkey(self, key):
        if isinstance(key, six.string_types):
            key = six.moves.StringIO(key)
        errors = []
        for key_class in (paramiko.rsakey.RSAKey, paramiko.dsskey.DSSKey):
            try:
                return key_class.from_private_key(key)
            except paramiko.SSHException as e:
                errors.append(e)
        raise SSHError("Invalid pkey: %s" % (errors))

    def _get_client(self):
        if self._client:
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
                       "during connect. Exception value is: %(exception)r")
            self._client = False
            raise SSHError(message % {"exception": e,
                                      "exception_type": type(e)})

    def close(self):
        self._client.close()
        self._client = False

    def run(self, cmd, stdin=None, stdout=None, stderr=None,
            raise_on_error=True, timeout=3600):
        """Execute specified command on the server.

        :param cmd:             Command to be executed.
        :param stdin:           Open file or string to pass to stdin.
        :param stdout:          Open file to connect to stdout.
        :param stderr:          Open file to connect to stderr.
        :param raise_on_error:  If False then exit code will be return. If True
                                then exception will be raized if non-zero code.
        :param timeout:         Timeout in seconds for command execution.
                                Default 1 hour. No timeout if set to 0.
        """

        client = self._get_client()

        if isinstance(stdin, six.string_types):
            stdin = six.moves.StringIO(stdin)

        return self._run(client, cmd, stdin=stdin, stdout=stdout,
                         stderr=stderr, raise_on_error=raise_on_error,
                         timeout=timeout)

    def _run(self, client, cmd, stdin=None, stdout=None, stderr=None,
             raise_on_error=True, timeout=3600):

        transport = client.get_transport()
        session = transport.open_session()
        session.exec_command(cmd)
        start_time = time.time()

        data_to_send = ""
        stderr_data = None

        # If we have data to be sent to stdin then `select' should also
        # check for stdin availability.
        if stdin and not stdin.closed:
            writes = [session]
        else:
            writes = []

        while True:
            # Block until data can be read/write.
            r, w, e = select.select([session], writes, [session], 1)

            if session.recv_ready():
                data = session.recv(4096)
                self.log.debug("stdout: %r" % data)
                if stdout is not None:
                    stdout.write(data)
                continue

            if session.recv_stderr_ready():
                stderr_data = session.recv_stderr(4096)
                self.log.debug("stderr: %r" % stderr_data)
                if stderr is not None:
                    stderr.write(stderr_data)
                continue

            if session.send_ready():
                if stdin is not None and not stdin.closed:
                    if not data_to_send:
                        data_to_send = stdin.read(4096)
                        if not data_to_send:
                            stdin.close()
                            session.shutdown_write()
                            writes = []
                            continue
                    sent_bytes = session.send(data_to_send)
                    # LOG.debug("sent: %s" % data_to_send[:sent_bytes])
                    data_to_send = data_to_send[sent_bytes:]

            if session.exit_status_ready():
                break

            if timeout and (time.time() - timeout) > start_time:
                args = {"cmd": cmd, "host": self.host}
                raise SSHTimeout("Timeout executing command "
                                 "'%(cmd)s' on host %(host)s" % args)
            if e:
                raise SSHError("Socket error.")

        exit_status = session.recv_exit_status()
        if 0 != exit_status and raise_on_error:
            fmt = "Command '%(cmd)s' failed with exit_status %(status)d."
            details = fmt % {"cmd": cmd, "status": exit_status}
            if stderr_data:
                details += " Last stderr data: '%s'." % stderr_data
            raise SSHError(details)
        return exit_status

    def execute(self, cmd, stdin=None, timeout=3600):
        """Execute the specified command on the server.

        :param cmd:     Command to be executed.
        :param stdin:   Open file to be sent on process stdin.
        :param timeout: Timeout for execution of the command.

        :returns: tuple (exit_status, stdout, stderr)
        """
        stdout = six.moves.StringIO()
        stderr = six.moves.StringIO()

        exit_status = self.run(cmd, stderr=stderr,
                               stdout=stdout, stdin=stdin,
                               timeout=timeout, raise_on_error=False)
        stdout.seek(0)
        stderr.seek(0)
        return (exit_status, stdout.read(), stderr.read())

    def wait(self, timeout=120, interval=1):
        """Wait for the host will be available via ssh."""
        start_time = time.time()
        while True:
            try:
                return self.execute("uname")
            except (socket.error, SSHError) as e:
                self.log.debug("Ssh is still unavailable: %r" % e)
                time.sleep(interval)
            if time.time() > (start_time + timeout):
                raise SSHTimeout("Timeout waiting for '%s'" % self.host)

    def put(self, files, remote_path=b'.', recursive=False):
        client = self._get_client()

        with SCPClient(client.get_transport()) as scp:
            scp.put(files, remote_path, recursive)

    # keep shell running in the background, e.g. screen
    def send_command(self, command):
        client = self._get_client()
        client.exec_command(command, get_pty=True)
