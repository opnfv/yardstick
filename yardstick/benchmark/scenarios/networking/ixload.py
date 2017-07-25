# Copyright 2016-2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import
from __future__ import print_function

import logging

import pkg_resources
from oslo_serialization import jsonutils
import time

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base
import logging
import os
import sys
import argparse
import re
import time
import datetime
import shutil
import unittest
import locale
import copy
import glob
import subprocess
import ast
import xmlrunner
import tempfile
import multiprocessing
from multiprocessing import Queue
from yardstick.traffic_generator.conf import settings
from yardstick.traffic_generator.core import component_factory
from yardstick.traffic_generator.core.loader import Loader
from yardstick.traffic_generator.tools import tasks
from yardstick.traffic_generator.tools import functions
from yardstick.traffic_generator.tools.pkt_gen import trafficgen
from yardstick.common.constants import YARDSTICK_ROOT_PATH

LOG = logging.getLogger(__name__)

VFW_PIPELINE_COMMAND = "/usr/bin/vFW -p 0x3 -f /tmp/vfw_config -s /tmp/vfw_script"
WAIT_TIME = 10
VFW_CONFIG = """
[PIPELINE0]
type = MASTER
core = 0

[PIPELINE1]
type = ARPICMP
core = 1
pktq_in = SWQ0
pktq_out = TXQ0.0 TXQ1.0

pktq_in_prv = RXQ0.0
prv_to_pub_map = (0, 1)

[PIPELINE2]
type = TXRX
core = 2
pipeline_txrx_type = RXRX
dest_if_offset = 176
pktq_in = RXQ0.0 RXQ1.0
pktq_out = SWQ1 SWQ2 SWQ0

[PIPELINE3]
type = LOADB
core = 3
pktq_in = SWQ1 SWQ2
pktq_out = SWQ3 SWQ4
outport_offset = 136
n_vnf_threads = 1
n_lb_tuples = 5
loadb_debug = 0
lib_arp_debug = 0
prv_que_handler = (0,)

[PIPELINE4]
type = VFW
core = 4
pktq_in = SWQ3 SWQ4
pktq_out = SWQ5 SWQ6
n_rules = 10
prv_que_handler = (0)
n_flows = 2000000
traffic_type = 4
pkt_type = ipv4
tcp_be_liberal = 0

[PIPELINE5]
type = TXRX
core = 5
pipeline_txrx_type = TXTX
dest_if_offset = 176
pktq_in = SWQ5 SWQ6
pktq_out = TXQ0.1 TXQ1.1
"""

VFW_SCRIPT="""
link 0 down
link 0 config 152.16.100.10 24
link 0 up
link 1 down
link 1 config 152.40.40.10 24
link 1 up

p action add 0 accept
p action add 0 fwd 0
p action add 0 count
p action add 1 accept
p action add 1 fwd 1
p action add 1 count
p action add 0 conntrack
p action add 1 conntrack

p acl add 1 152.16.100.0 24 152.40.40.0 24 0 65535 0 65535 17 255 1
p acl add 1 152.40.40.0 24 152.16.100.0 24 0 65535 0 65535 17 255 0
p vfw add 1 152.40.40.0 24 0.0.0.0 0 0 65535 0 65535 0 0 0
p vfw add 1 0.0.0.0 0 152.40.40.0 24 0 65535 0 65535 0 0 1

p vfw add 1 0.0.0.0 0 152.16.100.0 24 0 65535 0 65535 0 0 0
p vfw add 1 152.16.100.0 24 0.0.0.0 0 0 65535 0 65535 0 0 1
p vfw add 1 152.16.100.0 24 152.40.40.0 24 0 65535 0 65535 0 0 1
p vfw add 1 152.40.40.0 24 152.16.100.0 24 152.16.100.0 24 0 65535 0 65535 0 0 0

p vfw applyruleset

# adding arp route table
routeadd 0 152.16.100.20 0xFFFFFF00
routeadd 1 152.40.40.20 0xFFFFFF00
"""
class QueueFileWrapper(object):
    """ Class providing file-like API for talking with SSH connection """

    def __init__(self, q_in, q_out, prompt):
        self.q_in = q_in
        self.q_out = q_out
        self.closed = False
        self.buf = []
        self.bufsize = 20
        self.prompt = prompt

    def read(self, size):
        """ read chunk from input queue """
        if self.q_in.qsize() > 0 and size:
            in_data = self.q_in.get()
            return in_data

    def write(self, chunk):
        """ write chunk to output queue """
        self.buf.append(chunk)
        # flush on prompt or if we exceed bufsize

        size = sum(len(c) for c in self.buf)
        if self.prompt in chunk or size > self.bufsize:
            out = ''.join(self.buf)
            self.buf = []
            self.q_out.put(out)

    def close(self):
        """ close multiprocessing queue """
        pass

    def clear(self):
        """ clear queue """
        while self.q_out.qsize() > 0:
            self.q_out.get()


class Ixloadgen(base.Scenario):
    """Execute ixloadgen between two hosts

  Parameters
    packetsize - packet size in bytes without the CRC
        type:    int
        unit:    bytes
        default: 60
    number_of_ports - number of UDP ports to test
        type:    int
        unit:    na
        default: 10
    duration - duration of the test
        type:    int
        unit:    seconds
        default: 20
    """
    __scenario_type__ = "Ixloadgen"

    TARGET_SCRIPT = 'vfw_benchmark.bash'

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.q_in = Queue()
        self.q_out = Queue()
        self._vnf_process = None

    def _provide_config_file(self, prefix, template, args={}):
        cfg, cfg_content = tempfile.mkstemp()
        cfg = os.fdopen(cfg, "w+")
        cfg.write(template.format(**args))
        cfg.close()
        cfg_file = "/tmp/%s" % prefix
        self.server.put(cfg_content, cfg_file)
        return cfg_file

    def _run_vfw(self, filewrapper, target, options):
        self.server = ssh.SSH.from_node(target, defaults={"user": "ubuntu"})
        self.server.wait(timeout=600)
        # copy script to target
        self._provide_config_file("vfw_config", VFW_CONFIG)
        self._provide_config_file("vfw_script", VFW_SCRIPT)
        self.server._put_file_shell(self.target_script, '~/firewall_vnf.sh')
        cmd = "sudo -E bash ~/firewall_vnf.sh %s " % (' '.join(str(x) for x in options["pci"]))
        self.server.execute("pkill -9 vFW")
        self.server.run(VFW_PIPELINE_COMMAND, stdin=filewrapper, stdout=filewrapper,
                            keep_stdin_open=True, pty=True)

    def setup(self):
        """scenario setup"""
        self.target_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Ixloadgen.TARGET_SCRIPT)
        host = self.context_cfg['host']
        target = self.context_cfg['target']
        options = self.scenario_cfg["options"]

        LOG.info("user:%s, target:%s", target['user'], target['ip'])
        self.server = ssh.SSH.from_node(target, defaults={"user": "ubuntu"})
        self.server.wait(timeout=600)
        self.setup_done = True

        queue_wrapper = \
            QueueFileWrapper(self.q_in, self.q_out, "pipeline>")
        self._vnf_process = multiprocessing.Process(target=self._run_vfw,
                                                    args=(queue_wrapper,
                                                          target, options))
        self._vnf_process.start()
        buf = []
        time.sleep(WAIT_TIME)  # Give some time for config to load
        while True:
            message = ''
            while self.q_out.qsize() > 0:
                buf.append(self.q_out.get())
                message = ''.join(buf)
                if "pipeline>" in message:
                    LOG.info("VFW VNF is up and running.")
                    queue_wrapper.clear()
                    return self._vnf_process.exitcode
                if "PANIC" in message:
                    raise RuntimeError("Error starting vFW VNF.")

            LOG.info("Waiting for vFW VNF to start.. ")
            time.sleep(3)
            if not self._vnf_process.is_alive():
                raise RuntimeError("vFW VNF process died.")

    def run(self, result):
        """execute the benchmark"""

        if not self.setup_done:
            self.setup()
        time.sleep(WAIT_TIME)  # Give some time for config to load

        path = os.path.join(YARDSTICK_ROOT_PATH,
                            "yardstick", "traffic_generator")
        settings.load_from_dir(os.path.join(path, 'conf'))
        LOG.debug(self.scenario_cfg["options"].get("args", {}))
        settings.load_from_dict(self.scenario_cfg["options"].get("args", {}))
        settings.setValue('mode', 'trafficgen')
        trafficgens = Loader().get_trafficgens()
        loader = Loader()
        traffic = copy.deepcopy(settings.getValue('TRAFFIC'))
        traffic = functions.check_traffic(traffic)

        traffic_ctl = component_factory.create_traffic(
                      traffic['traffic_type'],
                      loader.get_trafficgen_class())
        with traffic_ctl:
            traffic_ctl.send_traffic(traffic)
        LOG.debug("Traffic Results:")
        traffic_ctl.print_results()

        LOG.debug(traffic_ctl._results)
        result.update({"http_tests": traffic_ctl._results})
        self.server.execute("pkill -9 vFW")
        if self._vnf_process:
            self._vnf_process.terminate()

def _test():
    """internal test function"""
    key_filename = pkg_resources.resource_filename('yardstick.resources',
                                                   'files/yardstick_key')
    ctx = {
        'host': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename
        },
        'target': {
            'ip': '10.229.47.137',
            'user': 'root',
            'key_filename': key_filename,
            'ipaddr': '10.229.47.137',
        }
    }

    logger = logging.getLogger('yardstick')
    logger.setLevel(logging.DEBUG)

    options = {'packetsize': 120}
    args = {'options': options}
    result = {}

    p = Ixloadgen(args, ctx)
    p.run(result)
    print(result)


if __name__ == '__main__':
    _test()
