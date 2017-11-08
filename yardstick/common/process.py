# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import multiprocessing
import signal
import subprocess
import time

import os
from oslo_utils import encodeutils

from yardstick.common import exceptions
from yardstick.common import utils


LOG = logging.getLogger(__name__)


def check_if_process_failed(proc, timeout=1):
    if proc is not None:
        proc.join(timeout)
        # Only abort if the process aborted
        if proc.exitcode is not None and proc.exitcode > 0:
            raise RuntimeError("{} exited with status {}".format(proc.name, proc.exitcode))


def terminate_children(timeout=3):
    current_proccess = multiprocessing.current_process()
    active_children = multiprocessing.active_children()
    if not active_children:
        LOG.debug("no children to terminate")
        return
    for child in active_children:
        LOG.debug("%s %s %s, child: %s %s", current_proccess.name, current_proccess.pid,
                  os.getpid(), child, child.pid)
        LOG.debug("joining %s", child)
        child.join(timeout)
        child.terminate()
    active_children = multiprocessing.active_children()
    if not active_children:
        LOG.debug("no children to terminate")
    for child in active_children:
        LOG.debug("%s %s %s, after terminate child: %s %s", current_proccess.name,
                  current_proccess.pid, os.getpid(), child, child.pid)


def _addl_env_args(addl_env):
    """Build arguments for adding additional environment vars with env"""
    if addl_env is None:
        return []
    return ['env'] + ['%s=%s' % pair for pair in addl_env.items()]


def _subprocess_setup():
    # Python installs a SIGPIPE handler by default. This is usually not what
    # non-Python subprocesses expect.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def subprocess_popen(args, stdin=None, stdout=None, stderr=None, shell=False,
                     env=None, preexec_fn=_subprocess_setup, close_fds=True):
    return subprocess.Popen(args, shell=shell, stdin=stdin, stdout=stdout,
                            stderr=stderr, preexec_fn=preexec_fn,
                            close_fds=close_fds, env=env)


def create_process(cmd, run_as_root=False, addl_env=None):
    """Create a process object for the given command.

    The return value will be a tuple of the process object and the
    list of command arguments used to create it.
    """
    cmd = list(map(str, _addl_env_args(addl_env) + cmd))
    if run_as_root:
        # TODO(ralonsoh): to handle the execution of a command as root, using
        # a root wrapper, instead of using "sudo".
        pass
    LOG.debug("Running command: %s", cmd)
    obj = subprocess_popen(cmd, shell=False, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return obj, cmd


def execute(cmd, process_input=None, addl_env=None,
            check_exit_code=True, return_stderr=False, log_fail_as_error=True,
            extra_ok_codes=None, run_as_root=False):
    try:
        if process_input is not None:
            _process_input = encodeutils.to_utf8(process_input)
        else:
            _process_input = None

        # TODO(ralonsoh): to handle the execution of a command as root,
        # using a root wrapper, instead of using "sudo".
        obj, cmd = create_process(cmd, run_as_root=run_as_root,
                                  addl_env=addl_env)
        _stdout, _stderr = obj.communicate(_process_input)
        returncode = obj.returncode
        obj.stdin.close()
        _stdout = utils.safe_decode_utf8(_stdout)
        _stderr = utils.safe_decode_utf8(_stderr)

        extra_ok_codes = extra_ok_codes or []
        if returncode and returncode not in extra_ok_codes:
            msg = ("Exit code: %(returncode)d; "
                   "Stdin: %(stdin)s; "
                   "Stdout: %(stdout)s; "
                   "Stderr: %(stderr)s") % {
                        'returncode': returncode,
                        'stdin': process_input or '',
                        'stdout': _stdout,
                        'stderr': _stderr}
            if log_fail_as_error:
                LOG.error(msg)
            if check_exit_code:
                raise exceptions.ProcessExecutionError(msg,
                                                       returncode=returncode)

    finally:
        # This appears is be necessary to let the subprocess call clean
        # something up in between calls, without it two execute calls in a row
        # hangs the second one.
        time.sleep(0)

    return (_stdout, _stderr) if return_stderr else _stdout
