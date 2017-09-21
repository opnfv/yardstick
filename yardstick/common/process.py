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

import os

LOG = logging.getLogger(__name__)


def check_if_process_exited(proc, timeout=1):
    if proc is not None:
        proc.join(timeout)
        if proc.exitcode is not None:
            raise RuntimeError("{} exited with status {}".format(proc.name, proc.exitcode))


def make_exitable_queue(*args, **kwargs):
    """
    Call cancel_join_thread() so we can always exit without Queue flush
    """
    q = multiprocessing.Queue(*args, **kwargs)
    # allow_exit_without_flush
    q.cancel_join_thread()
    return q


class TerminatingProcess(multiprocessing.Process):
    def run(self):
        try:
            try:
                super(TerminatingProcess, self).run()
            finally:
                LOG.debug("%s %s %s terminating children", self.name, self.pid, os.getpid())
                # kill all the remaing children at this point
                terminate_children()
        # never pass exception back to multiprocessing, because some exceptions can
        # be unpicklable
        # https://bugs.python.org/issue9400
        except:
            LOG.exception("")
            # exit with simple exception
            raise SystemExit(1)

    def check_if_exited(self, timeout=1):
        self.join(timeout)
        if self.exitcode is not None:
            raise RuntimeError("{} exited with status {}".format(self.name, self.exitcode))


def terminate_children(timeout=3):
    current_proccess = multiprocessing.current_process()
    active_children = multiprocessing.active_children()
    if not active_children:
        LOG.debug("no children to terminate")
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
