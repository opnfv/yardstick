##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import multiprocessing
import subprocess
import traceback
import time

LOG = logging.getLogger(__name__)


def _execute_shell_command(command):
    '''execute shell script with error handling'''
    exitcode = 0
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
    except Exception:
        exitcode = -1
        output = traceback.format_exc()
        LOG.error("exec command '%s' error:\n " % command)
        LOG.error(traceback.format_exc())

    return exitcode, output


def _monitor_process(config, queue, event):

    total_time = 0
    outage_time = 0
    total_count = 0
    outage_count = 0
    first_outage = 0
    last_outage = 0

    wait_time = config.get("duration", 0)
    cmd = config.get("monitor_cmd", None)
    if cmd is None:
        LOG.error("There are no monitor cmd!")
        return

    queue.put("started")

    begin_time = time.time()
    while True:

        total_count = total_count + 1

        one_check_begin_time = time.time()
        exit_status, stdout = _execute_shell_command(cmd)
        one_check_end_time = time.time()

        LOG.info("the exit_status:%s stdout:%s" % (exit_status, stdout))
        if exit_status:
            outage_count = outage_count + 1

            outage_time = outage_time + (
                one_check_end_time - one_check_begin_time)

            if not first_outage:
                first_outage = one_check_begin_time

            last_outage = one_check_end_time

        if event.is_set():
            LOG.debug("the monitor process stop")
            break

        if wait_time > 0:
            time.sleep(wait_time)

    end_time = time.time()
    total_time = end_time - begin_time

    queue.put({"total_time": total_time,
               "outage_time": last_outage-first_outage,
               "total_count": total_count,
               "outage_count": outage_count})


class Monitor:

    def __init__(self):
        self._result = []
        self._monitor_process = []

    def setup(self, config):
        self._config = config

    def start(self):
        self._queue = multiprocessing.Queue()
        self._event = multiprocessing.Event()
        self._monitor_process = multiprocessing.Process(
            target=_monitor_process, name="Monitor",
            args=(self._config, self._queue, self._event))

        self._monitor_process.start()
        ret = self._queue.get()
        if ret == "started":
            LOG.debug("monitor process started!")

    def stop(self):
        self._event.set()
        self._result = self._queue.get()
        LOG.debug("stop the monitor process. the result:%s" % self._result)

    def get_result(self):
        return self._result
