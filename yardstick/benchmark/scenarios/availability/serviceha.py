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

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
from yardstick.benchmark.scenarios.availability.monitor import Monitor

LOG = logging.getLogger(__name__)


class ServiceHA(base.Scenario):
    """TODO: docstring of ServiceHA
    """
    __scenario_type__ = "ServiceHA"

    FAULT_SCRIPT = "ha_tools/stop_service.bash"
    RECOVERY_SCRIPT = "ha_tools/start_service.bash"
    CHECK_SCRIPT = "ha_tools/status_service.bash"

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
        args["cmd"] = "nova image-list"
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
        "key_filename": "/root/.ssh/id_rsa"
    }
    ctx = {"host": host}

    logger = logging.getLogger("yardstick")
    logger.setLevel(logging.DEBUG)

    options = {
        "process_name": "nova-api"
    }
    sla = {"outage_time": 5}
    args = {"options": options, "sla": sla}

    print "create instance"
    terstInstance = ServiceHA(args, ctx)

    terstInstance.setup()
    result = terstInstance.run(None)
    print result

    terstInstance.teardown()

if __name__ == '__main__':
    _test()
