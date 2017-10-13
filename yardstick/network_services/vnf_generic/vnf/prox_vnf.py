# Copyright (c) 2017 Intel Corporation
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


from yardstick.common.process import check_if_process_failed
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxDpdkVnfSetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.prox_helpers import ProxResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF, PROCESS_JOIN_TIMEOUT

LOG = logging.getLogger(__name__)


class ProxApproxVnf(SampleVNF):

    APP_NAME = 'PROX'
    APP_WORD = 'PROX'
    PROX_MODE = "Workload"
    VNF_PROMPT = "PROX started"
    LUA_PARAMETER_NAME = "sut"

    def __init__(self, name, vnfd, setup_env_helper_type=None, resource_helper_type=None):
        if setup_env_helper_type is None:
            setup_env_helper_type = ProxDpdkVnfSetupEnvHelper

        if resource_helper_type is None:
            resource_helper_type = ProxResourceHelper

        super(ProxApproxVnf, self).__init__(name, vnfd, setup_env_helper_type,
                                            resource_helper_type)

    def _vnf_up_post(self):
        self.resource_helper.up_post()

    def vnf_execute(self, cmd, *args, **kwargs):
        # try to execute with socket commands
        # ignore socket errors, e.g. when using force_quit
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
        # we can't get KPIs if the VNF is down
        check_if_process_failed(self._vnf_process)

        if self.resource_helper is None:
            result = {
                "packets_in": 0,
                "packets_dropped": 0,
                "packets_fwd": 0,
                "collect_stats": {"core": {}},
            }
            return result

        # use all_ports so we only use ports matched in topology
        port_count = len(self.vnfd_helper.port_pairs.all_ports)
        if port_count not in {1, 2, 4}:
            raise RuntimeError("Failed ..Invalid no of ports .. "
                               "1, 2 or 4 ports only supported at this time")

        port_stats = self.vnf_execute('port_stats', range(port_count))
        try:
            rx_total = port_stats[6]
            tx_total = port_stats[7]
        except IndexError:
            LOG.error("port_stats parse fail %s", port_stats)
            # return empty dict so we don't mess up existing KPIs
            return {}

        result = {
            "packets_in": tx_total,
            "packets_dropped": abs(rx_total - tx_total),
            "packets_fwd": rx_total,
            # we share ProxResourceHelper with TG, but we want to collect
            # collectd KPIs here and not TG KPIs, so use a different method name
            "collect_stats": self.resource_helper.collect_collectd_kpi(),
        }
        LOG.debug("%s collect KPIs %s", self.APP_NAME, result)
        return result

    def _tear_down(self):
        # this should be standardized for all VNFs or removed
        self.setup_helper.tear_down()

    def terminate(self):
        # stop collectd first or we get pika errors?
        self.resource_helper.stop_collect()
        # try to quit with socket commands
        # pkill is not matching, debug with pgrep
        self.ssh_helper.execute("sudo pgrep -lax  %s" % self.setup_helper.APP_NAME)
        self.ssh_helper.execute("sudo ps aux | grep -i %s" % self.setup_helper.APP_NAME)
        if self._vnf_process.is_alive():
            self.vnf_execute("stop_all")
            self.vnf_execute("quit")
            # hopefully quit succeeds and socket closes, so ignore force_quit socket errors
            self.vnf_execute("force_quit", _ignore_errors=True)
        self.setup_helper.kill_vnf()
        self._tear_down()
        if self._vnf_process is not None:
            LOG.debug("joining before terminate %s", self._vnf_process.name)
            self._vnf_process.join(PROCESS_JOIN_TIMEOUT)
            self._vnf_process.terminate()
