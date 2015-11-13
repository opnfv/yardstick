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
import time

import yardstick.common.utils as utils

LOG = logging.getLogger(__name__)


class BaseMonitor(object):
    """docstring for BaseMonitor"""

    def __init__(self, config):
        self._config = config
        self.setup_done = False

    @staticmethod
    def get_monitor_cls(monitor_type):
        '''return monitor class of specified type'''

        for monitor in utils.itersubclasses(BaseMonitor):
            if monitor_type == monitor.__monitor_type__:
                return monitor
        raise RuntimeError("No such monitor_type %s" % monitor_type)

    def one_request(self):
        pass


class MonitorMgr(object):
    """docstring for MonitorMgr"""
    def __init__(self):
        super(MonitorMgr, self).__init__()
        self._monitor_list = []

    def setup(self, config):
        LOG.debug("monitorMgr config: %s" % config)
        monitor_cfg = config

        for cfg in monitor_cfg:
            monitor_instance = MonitorGroup()
            monitor_instance.setup(cfg)

            self._monitor_list.append(monitor_instance)

    def do_monitor(self):
        for _monotor_instace in self._monitor_list:
            _monotor_instace.start_monitor()

    def stop_monitor(self):
        for _monotor_instace in self._monitor_list:
            _monotor_instace.stop_monitor()

    def get_result(self):

        total_time = 0
        outage_time = 0
        total_count = 0
        outage_count = 0

        for _monotor_instace in self._monitor_list:
            _result = _monotor_instace.get_result()
            total_time += _result["total_time"]
            outage_time += _result["outage_time"]
            total_count += _result["total_count"]
            outage_count += _result["outage_count"]

        ret = {
            "total_time": total_time,
            "outage_time": outage_time,
            "total_count": total_count,
            "outage_count": outage_count
        }

        return ret


class MonitorGroup(object):

    def __init__(self):
        self._monitor_list = []
        self._queue = multiprocessing.Queue()
        self._event = multiprocessing.Event()
        self._result_list = []

    def setup(self, config):
        self._config = config
        monitor_type = config["monitor_type"]
        monitor_cls = BaseMonitor.get_monitor_cls(monitor_type)

        self._instance_count = config.get("instance_count", 1)
        for count in range(self._instance_count):
            monitor_instance = multiprocessing.Process(
                target=_monitor_process, name="Monitor",
                args=(monitor_cls, self._config, self._queue, self._event))
            self._monitor_list.append(monitor_instance)

    def start_monitor(self):
        for monitor_instance in self._monitor_list:
            monitor_instance.start()

    def stop_monitor(self):
        self._event.set()
        for monitor_instance in self._monitor_list:
            result = self._queue.get()
            self._result_list.append(result)

    def get_result(self):
        total_time = 0
        outage_time = 0
        total_count = 0
        outage_count = 0

        for _result in self._result_list:
            total_time += _result["total_time"]
            outage_time += _result["outage_time"]
            total_count += _result["total_count"]
            outage_count += _result["outage_count"]

        ret = {
            "total_time": total_time/self._instance_count,
            "outage_time": outage_time/self._instance_count,
            "total_count": total_count/self._instance_count,
            "outage_count": outage_count/self._instance_count
        }

        return ret


def _monitor_process(cls, config, queue, event):

    wait_time = config.get("wait_time", 0)
    duration = config.get("duration", 0)
    max_time = config.get("max_time", 1000)

    total_time = 0
    outage_time = 0
    total_count = 0
    outage_count = 0
    first_outage = 0
    last_outage = 0

    monitor_instance = cls(config)
    if wait_time > 0:
        time.sleep(wait_time)
    begin_time = time.time()
    while True:

        total_count = total_count + 1

        one_check_begin_time = time.time()
        exit_status = monitor_instance.one_request()
        one_check_end_time = time.time()

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

        if one_check_end_time - begin_time > max_time:
            LOG.debug("the monitor max_time finished and exit!")
            break

        if duration > 0:
            time.sleep(duration)

    end_time = time.time()
    total_time = end_time - begin_time

    queue.put({"total_time": total_time,
               "outage_time": last_outage-first_outage,
               "total_count": total_count,
               "outage_count": outage_count})
