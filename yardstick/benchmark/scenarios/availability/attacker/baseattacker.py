##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import pkg_resources
import multiprocessing
import time
import yaml
import logging
import os

import yardstick.common.utils as utils

LOG = logging.getLogger(__name__)

attacker_conf_path = pkg_resources.resource_filename(
    "yardstick.benchmark.scenarios.availability.attacker",
    "attacker_conf.yaml")


class AttackerMgr:

    # Attacker_CONF = "attacker_conf.yaml"

    def __init__(self):
        self.attackers_cfg = []
        with open(attacker_conf_path) as stream:
            self.attackers_cfg = yaml.load(stream)

        LOG.debug("ha_cfg content:%s" % self.attackers_cfg)

        self.attacker_list = []

    def setup(self, config):
        LOG.debug("attackerMgr config: %s" % config)
        attackers_cfg = config

        for cfg in attackers_cfg:
            service_name = cfg['service_name']
            fault_type = cfg['fault_type']
            service_cfg = self.attackers_cfg.get(service_name, None)
            if not service_cfg:
                LOG.error(
                    "The component %s can not be supported!" % service_name)
                return

            fault_cfg = []
            for fault in service_cfg:
                if fault["type"] == fault_type:
                    fault_cfg = fault
                    break
            if not fault_cfg:
                LOG.error(
                    "The fualt_type %s can not be supproted!" % fault_type)
                return
            LOG.debug("the fault_cfg :%s" % fault_cfg)

            cfg['fault_cfg'] = fault_cfg
            attackerInstance = BaseAttacker.get_attacker(cfg)

            self.attacker_list.append(attackerInstance)

    def do_attack(self):
        for attacker in self.attacker_list:
            attacker.start()

        for attacker in self.attacker_list:
            attacker.join()

    def stop_attack(self):
        for attacker in self.attacker_list:
            if attacker.is_alive():
                attacker.terminate()


class BaseAttacker(multiprocessing.Process):

    def __init__(self, config):
        multiprocessing.Process.__init__(self)
        self.config = config
        self.setup_done = False

    @staticmethod
    def get_attacker(attacker_cfg):
        '''return attacker instance of specified type'''
        attacker_type = attacker_cfg['fault_type']
        print utils.itersubclasses(BaseAttacker)
        print BaseAttacker.__subclasses__()
        for attacker in utils.itersubclasses(BaseAttacker):
            print attacker
            if attacker_type == attacker.__attacker_type__:
                return attacker(attacker_cfg)
        raise RuntimeError("No such runner_type %s" % attacker_type)

    def get_script_fullpath(self, path):
        base_path = os.path.dirname(attacker_conf_path)
        return os.path.join(base_path, path)

    def run(self):

        self._setup(self.config)

        if not self.setup_done:
            LOG.error("the attacker not set config!")
            return

        wait_time = self.config.get('wait_time', 0)
        fault_time = self.config.get('fault_time', 0)
        LOG.debug("wait_time:%s fault_time:%s" % (wait_time, fault_time))

        # 1.for the monitor prepare the enverioment
        LOG.info("waiting for %s seconds!" % wait_time)
        time.sleep(wait_time)

        # 2.inject the fault
        LOG.info("inject the fault!")
        self._inject_fault()
        LOG.info("inject fault success!")

        # 3.for the monitor check the service availability
        LOG.info("hold the fault for %s seconds!" % fault_time)
        time.sleep(fault_time)

        # 4.recovery the enverioment
        LOG.info("recover the enverioment!")
        self._recovery()
        LOG.info("recover the enverioment success!")
