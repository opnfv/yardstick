##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import logging
# import json
import multiprocessing
import subprocess
import traceback
import time

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

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

    queue.put("started")

    begin_time = time.time()
    while True:

        total_count = total_count + 1
        # print "execute the monitor cmd!"
        exit_status, stdout = _execute_shell_command("nova image-list")
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


class ServiceHA(base.Scenario):
    """TODO: docstring of ServiceHA
    """
    __scenario_type__ = "ServiceHA"

    FAULT_SCRIPT = "stop_service.bash"
    RECOVERY_SCRIPT = "start_service.bash"
    # CHECK_SCRIPT = "status_service.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.fault_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            ServiceHA.FAULT_SCRIPT)
        self.recovery_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            ServiceHA.RECOVERY_SCRIPT)
        self.check_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            ServiceHA.CHECK_SCRIPT)

        '''TODO: sometimes the envrioment is not ready.
           it should be add some pre-check codes.
        '''
        # user = self.context.get("user", "root")
        host = self.context_cfg.get("host", None)
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")
        LOG.info(
            "inject the host ip:%s, user:%s, key_file:",
            ip, user, key_filename)
        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait(timeout=600)
        LOG.debug(
            "ssh host success! ip:%s, user:%s, key_file:",
            ip, user, key_filename)

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        args = self.scenario_cfg
        service_name = args["options"]["process_name"]
        self.service_name = service_name

        # check the host envrioment
        # exit_status, stdout, stderr = self.connection.execute(
        #    "/bin/sh -s {0}".format(service_name),
        #    stdin=open(self.check_script, "r"))
        # if exit_status!=0 or stdout!="start"
        #    LOG.error("the host envrioment is error,
        #        stdout:%s, stderr:%s"%, stdout, stderr)
        #    return
        monitorInstance = Monitor()
        monitorInstance.setUp(args)
        monitorInstance.start()

        print "inject the fault! options:", args["options"]
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(service_name),
            stdin=open(self.fault_script, "r"))

        if exit_status != 0:
            monitorInstance.stop()
            raise RuntimeError(stderr)

        time.sleep(5)

        print "monitor process stop"
        monitorInstance.stop()

        ret = monitorInstance.get_result()
        outage_time = ret.get("outage_time")

        if "sla" in args:
            sla_outage_time = int(args["sla"]["outage_time"])
            assert outage_time <= sla_outage_time, "outage_time %f > sla:outage_time(%f)" % \
                (outage_time, sla_outage_time)

        return outage_time

    def teardown(self):
        '''scenario teardown'''
        print "recory the everiment!"

        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0} ".format(self.service_name),
            stdin=open(self.recovery_script, "r"))

        if exit_status:
            raise RuntimeError(stderr)


def _test():
    '''internal test function'''
    # key_filename = pkg_resources.resource_filename("yardstick.resources",
    #                                               "files/yardstick_key")
    host = {
        "ip": "10.20.0.5",
        "user": "root",
        "key_filename": "/root/yardstick/etc/id_rsa"
    }
    ctx = {"host": host}

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    print "create instance"
    terstInstance = ServiceHA(ctx)

    terstInstance.setup()

    options = {
        "process_name": "nova-api"
    }
    sla = {"outage_time": 5}
    args = {"options": options, "sla": sla}

    result = terstInstance.run(args, None)
    print result

    terstInstance.teardown()

if __name__ == '__main__':
    _test()
