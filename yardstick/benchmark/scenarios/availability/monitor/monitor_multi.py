##############################################################################
# Copyright (c) 2017 Huan Li and others
# lihuansse@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import logging
import time

from yardstick.benchmark.scenarios.availability.monitor import basemonitor

LOG = logging.getLogger(__name__)


class MultiMonitor(basemonitor.BaseMonitor):

    __monitor_type__ = "multi-monitor"

    def __init__(self, config, context):
        super(MultiMonitor, self).__init__(config, context)

        self.monitors = []
        monitor_type = self._config["monitor_type"]
        monitor_cls = basemonitor.BaseMonitor.get_monitor_cls(monitor_type)

        monitor_number = self._config.get("monitor_number", 1)
        for i in range(monitor_number):
            monitor_ins = monitor_cls(self._config, self._context)
            self.monitors.append(monitor_ins)

    def start_monitor(self):
        for monitor in self.monitors:
            monitor.start_monitor()

    def wait_monitor(self):
        for monitor in self.monitors:
            monitor.wait_monitor()

    def verify_SLA(self):
        first_outage = time.time()
        last_outage = 0

        for monitor in self.monitors:
            monitor_result = monitor.result()
            monitor_first_outage = monitor_result.get('first_outage', None)
            monitor_last_outage = monitor_result.get('last_outage', None)

            if monitor_first_outage is None or monitor_last_outage is None:
                continue

            if monitor_first_outage < first_outage:
                first_outage = monitor_first_outage

            if monitor_last_outage > last_outage:
                last_outage = monitor_last_outage
        LOG.debug("multi monitor result: %f , %f", first_outage, last_outage)

        outage_time = last_outage - first_outage
        max_outage_time = self._config["sla"]["max_outage_time"]
        if outage_time > max_outage_time:
            LOG.error("SLA failure: %f > %f", outage_time, max_outage_time)
            return False
        else:
            return True
