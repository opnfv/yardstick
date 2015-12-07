##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import time
from yardstick.benchmark.scenarios import base
from yardstick.benchmark.scenarios.availability import monitor
from yardstick.benchmark.scenarios.availability.attacker import baseattacker

LOG = logging.getLogger(__name__)


class ServiceHA(base.Scenario):
    """TODO: docstring of ServiceHA
    """
    __scenario_type__ = "ServiceHA"

    def __init__(self, scenario_cfg, context_cfg):
        LOG.debug(
            "scenario_cfg:%s context_cfg:%s" %
            (scenario_cfg, context_cfg))
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        nodes = self.context_cfg.get("nodes", None)
        if nodes is None:
            LOG.error("the nodes info is none")
            return
        self.wait_time = self.scenario_cfg["options"]["wait_time"]
        self.attackers = []
        attacker_cfgs = self.scenario_cfg["options"]["attackers"]
        for attacker_cfg in attacker_cfgs:
            attacker_cls = baseattacker.BaseAttacker.get_attacker_cls(
                attacker_cfg)
            attacker_ins = attacker_cls(attacker_cfg, nodes)
            attacker_ins.setup()
            print attacker_ins
            self.attackers.append(attacker_ins)

        monitor_cfgs = self.scenario_cfg["options"]["monitors"]

        self.monitorInstance = monitor.Monitor()
        self.monitorInstance.setup(monitor_cfgs[0])
        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        if not self.setup_done:
            LOG.error("The setup not finished!")
            return

        self.monitorInstance.start()
        LOG.info("monitor start!")

        for attacker in self.attackers:
            attacker.inject_fault()

        time.sleep(self.wait_time)

        self.monitorInstance.stop()
        LOG.info("monitor stop!")

        ret = self.monitorInstance.get_result()
        LOG.info("The monitor result:%s" % ret)
        outage_time = ret.get("outage_time")
        result["outage_time"] = outage_time
        LOG.info("the result:%s" % result)

        if "sla" in self.scenario_cfg:
            sla_outage_time = int(self.scenario_cfg["sla"]["outage_time"])
            assert outage_time <= sla_outage_time, "outage_time %f > sla:outage_time(%f)" % \
                (outage_time, sla_outage_time)

        return

    def teardown(self):
        '''scenario teardown'''
        for attacker in self.attackers:
            attacker.recover()
