# Copyright (c) 2018-2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import logging
import copy
import time

from yardstick.common.process import check_if_process_failed
from yardstick.network_services.utils import get_nsb_option
from yardstick.network_services.vnf_generic.vnf.prox_vnf import ProxApproxVnf
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNFTrafficGen
from yardstick.benchmark.contexts.base import Context
from yardstick.network_services.vnf_generic.vnf.prox_helpers import CoreSocketTuple
LOG = logging.getLogger(__name__)


class ProxIrq(SampleVNFTrafficGen):

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        vnfd_cpy = copy.deepcopy(vnfd)
        super(ProxIrq, self).__init__(name, vnfd_cpy)

        self._vnf_wrapper = ProxApproxVnf(
            name, vnfd, setup_env_helper_type, resource_helper_type)
        self.bin_path = get_nsb_option('bin_path', '')
        self.name = self._vnf_wrapper.name
        self.ssh_helper = self._vnf_wrapper.ssh_helper
        self.setup_helper = self._vnf_wrapper.setup_helper
        self.resource_helper = self._vnf_wrapper.resource_helper
        self.scenario_helper = self._vnf_wrapper.scenario_helper
        self.irq_cores = None

    def terminate(self):
        self._vnf_wrapper.terminate()
        super(ProxIrq, self).terminate()

    def instantiate(self, scenario_cfg, context_cfg):
        self._vnf_wrapper.instantiate(scenario_cfg, context_cfg)
        self._tg_process = self._vnf_wrapper._vnf_process

    def wait_for_instantiate(self):
        self._vnf_wrapper.wait_for_instantiate()

    def get_irq_cores(self):
        cores = []
        mode = "irq"

        for section_name, section in self.setup_helper.prox_config_data:
            if not section_name.startswith("core"):
                continue
            irq_mode = task_present = False
            task_present_task = 0
            for key, value in section:
                if key == "mode" and value == mode:
                    irq_mode = True
                if key == "task":
                    task_present = True
                    task_present_task = int(value)

            if irq_mode:
                if not task_present:
                    task_present_task = 0
                core_tuple = CoreSocketTuple(section_name)
                core = core_tuple.core_id
                cores.append((core, task_present_task))

        return cores

class ProxIrqVNF(ProxIrq, SampleVNFTrafficGen):

    APP_NAME = 'ProxIrqVNF'

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        ProxIrq.__init__(self, name, vnfd, setup_env_helper_type,
                        resource_helper_type)

        self.start_test_time = None
        self.end_test_time = None

    def vnf_execute(self, cmd, *args, **kwargs):
        ignore_errors = kwargs.pop("_ignore_errors", False)
        try:
            return self.resource_helper.execute(cmd, *args, **kwargs)
        except OSError as e:
            if e.errno in {errno.EPIPE, errno.ESHUTDOWN, errno.ECONNRESET}:
                if ignore_errors:
                    LOG.debug("ignoring vnf_execute exception %s for command %s", e, cmd)
                else:
                    raise
            else:
                raise

    def collect_kpi(self):
        # check if the tg processes have exited
        physical_node = Context.get_physical_node_from_server(
            self.scenario_helper.nodes[self.name])

        result = {"physical_node": physical_node}
        for proc in (self._tg_process, self._traffic_process):
            check_if_process_failed(proc)

        if self.resource_helper is None:
            return result

        if self.irq_cores is None:
            self.setup_helper.build_config_file()
            self.irq_cores = self.get_irq_cores()

        data = self.vnf_execute('irq_core_stats', self.irq_cores)
        new_data = copy.deepcopy(data)

        self.end_test_time = time.time()
        self.vnf_execute('reset_stats')

        if self.start_test_time is None:
            new_data = {}
        else:
            test_time = self.end_test_time - self.start_test_time
            for index, item in data.items():
                for counter, value in item.items():
                    if counter.startswith("bucket_")or \
                            counter.startswith("overflow"):
                        if value is 0:
                            del new_data[index][counter]
                        else:
                            new_data[index][counter] = float(value) / test_time

        self.start_test_time = time.time()

        result["collect_stats"] = new_data
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)

        return result

class ProxIrqGen(ProxIrq, SampleVNFTrafficGen):

    APP_NAME = 'ProxIrqGen'

    def __init__(self, name, vnfd, setup_env_helper_type=None,
                 resource_helper_type=None):
        ProxIrq.__init__(self, name, vnfd, setup_env_helper_type,
                                      resource_helper_type)
        self.start_test_time = None
        self.end_test_time = None

    def collect_kpi(self):
        # check if the tg processes have exited
        physical_node = Context.get_physical_node_from_server(
            self.scenario_helper.nodes[self.name])

        result = {"physical_node": physical_node}
        for proc in (self._tg_process, self._traffic_process):
            check_if_process_failed(proc)

        if self.resource_helper is None:
            return result

        if self.irq_cores is None:
            self.setup_helper.build_config_file()
            self.irq_cores = self.get_irq_cores()

        data = self.resource_helper.sut.irq_core_stats(self.irq_cores)
        new_data = copy.deepcopy(data)

        self.end_test_time = time.time()
        self.resource_helper.sut.reset_stats()

        if self.start_test_time is None:
            new_data = {}
        else:
            test_time = self.end_test_time - self.start_test_time
            for index, item in data.items():
                for counter, value in item.items():
                    if counter.startswith("bucket_") or \
                            counter.startswith("overflow"):
                        if value is 0:
                            del new_data[index][counter]
                        else:
                            new_data[index][counter] = float(value) / test_time

        self.start_test_time = time.time()

        result["collect_stats"] = new_data
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)

        return result
