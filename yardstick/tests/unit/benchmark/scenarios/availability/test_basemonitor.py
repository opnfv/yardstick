##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import unittest

from yardstick.benchmark.scenarios.availability.monitor import basemonitor


class MonitorMgrTestCase(unittest.TestCase):

    def setUp(self):
        self.monitor_configs = [
            {
                "monitor_type": "openstack-cmd",
                "command_name": "openstack router list",
                "monitor_time": 10,
                "monitor_number": 3,
                "sla": {
                    "max_outage_time": 5
                }
            },
            {
                "monitor_type": "process",
                "process_name": "neutron-server",
                "host": "node1",
                "monitor_time": 20,
                "monitor_number": 3,
                "sla": {
                    "max_recover_time": 20
                }
            }
        ]
        self.MonitorMgr = basemonitor.MonitorMgr([])
        self.MonitorMgr.init_monitors(self.monitor_configs, None)
        self.monitor_list = self.MonitorMgr._monitor_list
        for mo in self.monitor_list:
            mo._result = {"outage_time": 10}

    @mock.patch.object(basemonitor, 'BaseMonitor')
    def test__MonitorMgr_setup_successful(self, *args):
        instance = basemonitor.MonitorMgr({"nova-api": 10})
        instance.init_monitors(self.monitor_configs, None)
        instance.start_monitors()
        instance.wait_monitors()

        # TODO(elfoley): Check the return value
        ret = instance.verify_SLA()  # pylint: disable=unused-variable

    @mock.patch.object(basemonitor, 'BaseMonitor')
    def test_MonitorMgr_getitem(self, *args):
        monitorMgr = basemonitor.MonitorMgr({"nova-api": 10})
        monitorMgr.init_monitors(self.monitor_configs, None)

    @mock.patch.object(basemonitor, 'BaseMonitor')
    def test_store_result(self, *args):
        expect = {'process_neutron-server_outage_time': 10,
                  'openstack-router-list_outage_time': 10}
        result = {}
        self.MonitorMgr.store_result(result)
        self.assertDictEqual(result, expect)


class BaseMonitorTestCase(unittest.TestCase):

    class MonitorSimple(basemonitor.BaseMonitor):
        __monitor_type__ = "MonitorForTest"

        def setup(self):
            self.monitor_result = False

        def monitor_func(self):
            return self.monitor_result

    def setUp(self):
        self.monitor_cfg = {
            'monitor_type': 'MonitorForTest',
            'command_name': 'nova image-list',
            'monitor_time': 0.01,
            'sla': {'max_outage_time': 5}
        }

    def test__basemonitor_start_wait_successful(self):
        ins = basemonitor.BaseMonitor(self.monitor_cfg, None, {"nova-api": 10})
        ins.start_monitor()
        ins.wait_monitor()

    def test__basemonitor_all_successful(self):
        ins = self.MonitorSimple(self.monitor_cfg, None, {"nova-api": 10})
        ins.setup()
        ins.run()
        ins.verify_SLA()

    @mock.patch.object(basemonitor, 'multiprocessing')
    def test__basemonitor_func_false(self, mock_multiprocess):
        ins = self.MonitorSimple(self.monitor_cfg, None, {"nova-api": 10})
        ins.setup()
        mock_multiprocess.Event().is_set.return_value = False
        ins.run()
        ins.verify_SLA()

    # TODO(elfoley): fix this test to not throw an error
    def test__basemonitor_getmonitorcls_successfule(self):
        cls = None
        try:
            cls = basemonitor.BaseMonitor.get_monitor_cls(self.monitor_cfg)
        except Exception:  # pylint: disable=broad-except
            pass
        self.assertIsNone(cls)
