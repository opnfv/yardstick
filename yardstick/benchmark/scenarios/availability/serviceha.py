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
        host = self.context_cfg.get("host", None)

        attacker_cfgs = self.scenario_cfg["options"]["attackers"]
        for attacker_cfg in attacker_cfgs:
            attacker_cfg["host"] = host

        self.attacker_instance = baseattacker.AttackerMgr()
        self.attacker_instance.setup(attacker_cfgs)

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

        self.attacker_instance.do_attack()

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
        self.attacker_instance.stop_attack()


def _test():    # pragma: no cover
    '''internal test function'''
    host = {
        "ip": "10.20.0.5",
        "user": "root",
        "key_filename": "/root/.ssh/id_rsa"
    }
    ctx = {"host": host}
    attacker_cfg = {
        "fault_type": "stop-service",
        "service_name": "nova-api",
        "fault_time": 5,
        "host": host
    }
    attacker_cfgs = []
    attacker_cfgs.append(attacker_cfg)
    monitor_cfg = {
        "monitor_type": "openstack-api",
        "monitor_api": "nova image-list"
    }
    monitor_cfgs = []
    monitor_cfgs.append(monitor_cfg)

    options = {
        "attackers": attacker_cfgs,
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
