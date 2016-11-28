##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
from yardstick.benchmark.scenarios import base
from yardstick.benchmark.scenarios.availability.monitor import basemonitor
from yardstick.benchmark.scenarios.availability.attacker import baseattacker

LOG = logging.getLogger(__name__)


class ServiceHA(base.Scenario):
    """TODO: docstring of ServiceHA
    """
    __scenario_type__ = "ServiceHA"

    def __init__(self, scenario_cfg, context_cfg):
        LOG.debug(
            "scenario_cfg:%s context_cfg:%s",
            scenario_cfg, context_cfg)
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        nodes = self.context_cfg.get("nodes", None)
        if nodes is None:
            LOG.error("the nodes info is none")
            return

        self.attackers = []
        attacker_cfgs = self.scenario_cfg["options"]["attackers"]
        for attacker_cfg in attacker_cfgs:
            attacker_cls = baseattacker.BaseAttacker.get_attacker_cls(
                attacker_cfg)
            attacker_ins = attacker_cls(attacker_cfg, nodes)
            attacker_ins.setup()
            self.attackers.append(attacker_ins)

        monitor_cfgs = self.scenario_cfg["options"]["monitors"]

        self.monitorMgr = basemonitor.MonitorMgr()
        self.monitorMgr.init_monitors(monitor_cfgs, nodes)

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        if not self.setup_done:
            LOG.error("The setup not finished!")
            return

        self.monitorMgr.start_monitors()
        LOG.info("monitor start!")

        for attacker in self.attackers:
            attacker.inject_fault()

        self.monitorMgr.wait_monitors()
        LOG.info("monitor stop!")

        sla_pass = self.monitorMgr.verify_SLA()
        if sla_pass:
            result['sla_pass'] = 1
        else:
            result['sla_pass'] = 0
        assert sla_pass is True, "the test cases is not pass the SLA"

        return

    def teardown(self):
        '''scenario teardown'''
        for attacker in self.attackers:
            attacker.recover()


def _test():    # pragma: no cover
    '''internal test function'''
    host = {
        "ip": "10.20.0.5",
        "user": "root",
        "key_filename": "/root/.ssh/id_rsa"
    }
    ctx = {"nodes": {"node1": host}}
    attacker_cfg = {
        "fault_type": "kill-process",
        "process_name": "nova-api",
        "host": "node1"
    }
    attacker_cfgs = []
    attacker_cfgs.append(attacker_cfg)
    monitor_cfg = {
        "monitor_cmd": "nova image-list"
    }
    monitor_cfgs = []
    monitor_cfgs.append(monitor_cfg)

    options = {
        "attackers": attacker_cfgs,
        "wait_time": 10,
        "monitors": monitor_cfgs
    }
    sla = {"outage_time": 5}
    args = {"options": options, "sla": sla}

    print "create instance"
    terstInstance = ServiceHA(args, ctx)

    terstInstance.setup()
    result = {}
    terstInstance.run(result)
    print result

    terstInstance.teardown()

if __name__ == '__main__':    # pragma: no cover
    _test()
