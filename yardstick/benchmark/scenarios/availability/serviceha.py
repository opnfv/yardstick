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
import time
import yaml
import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
from yardstick.benchmark.scenarios.availability import monitor

LOG = logging.getLogger(__name__)


class ServiceHA(base.Scenario):
    """TODO: docstring of ServiceHA
    """
    __scenario_type__ = "ServiceHA"

    HA_CONF = "ha_tools/ha_conf.yaml"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.service_name = scenario_cfg["options"]["component"]
        self.fault_type = scenario_cfg["options"]["fault_type"]
        self.fault_time = scenario_cfg["options"].get("fault_time", 0)
        self.fault_cfg = None
        self.setup_done = False
        self.need_teardown = False

    def setup(self):
        '''scenario setup'''
        self.ha_conf_file = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            ServiceHA.HA_CONF)
        ha_cfg = []
        with open(self.ha_conf_file) as stream:
                ha_cfg = yaml.load(stream)
        LOG.debug("ha_cfg content:%s" % ha_cfg)

        # check the ha_conf contains the service defined in test cases yaml
        service_cfg = ha_cfg.get(self.service_name, None)
        if not service_cfg:
            LOG.error(
                "The component %s can not be supported!" % self.service_name)
            return

        for fault in service_cfg:
            if fault["type"] == self.fault_type:
                self.fault_cfg = fault
                break
        if not self.fault_cfg:
            LOG.error(
                "The fualt_type %s can not be supproted!" % self.fault_type)
            return
        LOG.debug("the fault_cfg :%s" % self.fault_cfg)

        self.fault_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            self.fault_cfg["inject_script"])
        self.recovery_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            self.fault_cfg["recovery_script"])
        self.check_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.availability",
            self.fault_cfg["check_script"])

        host = self.context_cfg.get("host", None)
        ip = host.get("ip", None)
        user = host.get("user", "root")
        key_filename = host.get("key_filename", "~/.ssh/id_rsa")
        LOG.info("The host: %s  the service: %s" % (ip, self.service_name))
        LOG.debug("The params, host:%s  fault_cfg:%s" % (host, self.fault_cfg))

        LOG.debug(
            "ssh connection ip:%s, user:%s, key_file:%s",
            ip, user, key_filename)
        self.connection = ssh.SSH(user, ip, key_filename=key_filename)
        self.connection.wait(timeout=600)
        LOG.debug("ssh host success!")

        # check the host envrioment
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(self.service_name),
            stdin=open(self.check_script, "r"))
        LOG.info(
            "the exit_status:%s stdout:%s stderr:%s" %
            (exit_status, stdout, stderr))
        if exit_status:
            raise RuntimeError(stderr)

        if stdout and "running" in stdout:
            LOG.info("check the envrioment success!")
        else:
            LOG.error(
                "the host envrioment is error, stdout:%s, stderr:%s" %
                (stdout, stderr))
            return

        self.setup_done = True

    def run(self, result):
        """execute the benchmark"""
        if not self.setup_done:
            LOG.error("The setup not finished!")
            return

        monitorInstance = monitor.Monitor()
        monitorInstance.setup(self.fault_cfg)
        monitorInstance.start()
        LOG.info("monitor start!")

        LOG.info("Inject fault!")
        exit_status, stdout, stderr = self.connection.execute(
            "/bin/sh -s {0}".format(self.service_name),
            stdin=open(self.fault_script, "r"))

        if exit_status != 0:
            monitorInstance.stop()
            raise RuntimeError(stderr)

        self.need_teardown = True
        time.sleep(self.fault_time)

        monitorInstance.stop()
        LOG.info("monitor stop!")

        ret = monitorInstance.get_result()
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
        LOG.info("recory the everiment!")

        if self.need_teardown:
            exit_status, stdout, stderr = self.connection.execute(
                "/bin/sh -s {0} ".format(self.service_name),
                stdin=open(self.recovery_script, "r"))

            if exit_status:
                raise RuntimeError(stderr)
            else:
                self.need_teardown = False

"""
def _test():
    '''internal test function'''
    host = {
        "ip": "10.20.0.5",
        "user": "root",
        "key_filename": "/root/.ssh/id_rsa"
    }
    ctx = {"host": host}

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    options = {
        "component": "nova-api",
        "fault_type": "stop-service"
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

if __name__ == '__main__':
    _test()
"""
