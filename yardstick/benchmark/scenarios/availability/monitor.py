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

    is_outage = False

    wait_time = config.get("duration", 0)
    cmd = config.get("cmd", None)
    if cmd is None:
        print "There are no monitor cmd!"
        return

    queue.put("started")

    begin_time = time.time()
    while True:

        total_count = total_count + 1
        # print "execute the monitor cmd!"
        exit_status, stdout = _execute_shell_command(cmd)
        # print "finish the monitor cmd, exit_status:", exit_status
        if exit_status:
            outage_count = outage_count + 1
            if not is_outage:
                is_outage = True
                outage_begin_time = time.time()
        else:
            if is_outage:
                is_outage = False
                outage_end_time = time.time()
                outage_time = outage_time + (
                    outage_end_time - outage_begin_time)

        if event.is_set():
            print "the monitor process stop"
            break

        if wait_time > 0:
            time.sleep(wait_time)

    if is_outage:
        is_outage = False
        outage_end_time = time.time()
        outage_time = outage_time + (outage_end_time - outage_begin_time)

    end_time = time.time()
    total_time = end_time - begin_time

    queue.put({"total_time": total_time,
               "outage_time": outage_time,
               "total_count": total_count,
               "outage_count": outage_count})


class Monitor:

    def __init__(self):
        self._result = []
        self._monitor_process = []

    def setUp(self, config):
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
            print "monitor process started!"

    def stop(self):
        self._event.set()
        self._result = self._queue.get()
        print "the result of monitor:", self._result

    def get_result(self):
        return self._result
