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
