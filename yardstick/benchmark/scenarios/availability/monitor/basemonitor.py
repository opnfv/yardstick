##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
import pkg_resources
import logging
import multiprocessing
import time
import os
import yardstick.common.utils as utils

from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)

monitor_conf_path = pkg_resources.resource_filename(
    "yardstick.benchmark.scenarios.availability",
    "monitor_conf.yaml")


class MonitorMgr(object):
    """docstring for MonitorMgr"""

    def __init__(self, data):
        self._monitor_list = []
        self.monitor_mgr_data = data

    def init_monitors(self, monitor_cfgs, context):
        LOG.debug("monitorMgr config: %s", monitor_cfgs)

        for monitor_cfg in monitor_cfgs:
            monitor_type = monitor_cfg["monitor_type"]
            monitor_cls = BaseMonitor.get_monitor_cls(monitor_type)

            monitor_number = monitor_cfg.get("monitor_number", 1)
            if monitor_number > 1:
                monitor_cls = BaseMonitor.get_monitor_cls("multi-monitor")

            monitor_ins = monitor_cls(monitor_cfg, context,
                                      self.monitor_mgr_data)
            if "key" in monitor_cfg:
                monitor_ins.key = monitor_cfg["key"]
            self._monitor_list.append(monitor_ins)

    def __getitem__(self, item):
        for obj in self._monitor_list:
            if obj.key == item:
                return obj
        raise KeyError("No such monitor instance of key - %s" % item)

    def start_monitors(self):
        for _monotor_instace in self._monitor_list:
            _monotor_instace.start_monitor()

    def wait_monitors(self):
        for monitor in self._monitor_list:
            monitor.wait_monitor()

    def verify_SLA(self):
        sla_pass = True
        for monitor in self._monitor_list:
            sla_pass = sla_pass & monitor.verify_SLA()
        return sla_pass


class BaseMonitor(multiprocessing.Process):
    """docstring for BaseMonitor"""
    monitor_cfgs = {}

    def __init__(self, config, context, data):
        if not BaseMonitor.monitor_cfgs:
            with open(monitor_conf_path) as stream:
                BaseMonitor.monitor_cfgs = yaml_load(stream)
        multiprocessing.Process.__init__(self)
        self._config = config
        self._context = context
        self._queue = multiprocessing.Queue()
        self._event = multiprocessing.Event()
        self.monitor_data = data
        self.setup_done = False

    @staticmethod
    def get_monitor_cls(monitor_type):
        """return monitor class of specified type"""

        for monitor in utils.itersubclasses(BaseMonitor):
            if monitor_type == monitor.__monitor_type__:
                return monitor
        raise RuntimeError("No such monitor_type %s" % monitor_type)

    def get_script_fullpath(self, path):
        base_path = os.path.dirname(monitor_conf_path)
        return os.path.join(base_path, path)

    def run(self):
        LOG.debug("config:%s context:%s", self._config, self._context)

        self.setup()
        monitor_time = self._config.get("monitor_time", 0)

        total_time = 0
        outage_time = 0
        total_count = 0
        outage_count = 0
        first_outage = 0
        last_outage = 0

        begin_time = time.time()
        while True:
            total_count = total_count + 1

            one_check_begin_time = time.time()
            exit_status = self.monitor_func()
            one_check_end_time = time.time()

            if exit_status is False:
                outage_count = outage_count + 1

                outage_time = outage_time + (
                    one_check_end_time - one_check_begin_time)

                if not first_outage:
                    first_outage = one_check_begin_time

                last_outage = one_check_end_time

            if self._event.is_set():
                LOG.debug("the monitor process stop")
                break

            if one_check_end_time - begin_time > monitor_time:
                LOG.debug("the monitor max_time finished and exit!")
                break

        end_time = time.time()
        total_time = end_time - begin_time

        self._queue.put({"total_time": total_time,
                         "outage_time": last_outage - first_outage,
                         "last_outage": last_outage,
                         "first_outage": first_outage,
                         "total_count": total_count,
                         "outage_count": outage_count})

    def start_monitor(self):
        self.start()

    def wait_monitor(self):
        self.join()
        self._result = self._queue.get()
        LOG.debug("the monitor result:%s", self._result)

    def setup(self):  # pragma: no cover
        pass

    def monitor_func(self):  # pragma: no cover
        pass

    def verify_SLA(self):
        pass

    def result(self):
        return self._result
