# Copyright (c) 2016-2017 Intel Corporation
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

import logging
import multiprocessing
import uuid

from yardstick.common import utils
from yardstick.network_services.libs.ixia_libs.ixnet import ixnet_api
from yardstick.network_services.vnf_generic.vnf import base as vnf_base
from yardstick.network_services.vnf_generic.vnf import sample_vnf


LOG = logging.getLogger(__name__)

WAIT_AFTER_CFG_LOAD = 10
WAIT_FOR_TRAFFIC = 30


class IxiaRfc2544Helper(sample_vnf.Rfc2544ResourceHelper):

    def is_done(self):
        return self.latency and self.iteration.value > 10


class IxiaResourceHelper(sample_vnf.ClientResourceHelper):

    LATENCY_TIME_SLEEP = 120
    DEFAULT_MAC = '00:00:00:00:00:00'

    def __init__(self, setup_helper, rfc_helper_type=None):
        super(IxiaResourceHelper, self).__init__(setup_helper)
        self.scenario_helper = setup_helper.scenario_helper

        self.client = ixnet_api.IxNextgen()

        if rfc_helper_type is None:
            rfc_helper_type = IxiaRfc2544Helper

        self.rfc_helper = rfc_helper_type(self.scenario_helper)
        self.uplink_ports = None
        self.downlink_ports = None
        self._port_macs = None
        self._iteration_index = 0
        self._connect()

    @property
    def port_macs(self):
        if self._port_macs:
            return self._port_macs
        self._port_macs = {}
        for port_name in self.vnfd_helper.port_pairs.all_ports:
            intf = self.vnfd_helper.find_interface(name=port_name)
            virt_intf = intf['virtual-interface']
            port_num = self.vnfd_helper.port_num(intf)
            self._port_macs['src_mac_{}'.format(port_num)] = virt_intf.get(
                'local_mac', self.DEFAULT_MAC)
            self._port_macs['dst_mac_{}'.format(port_num)] = virt_intf.get(
                'dst_mac', self.DEFAULT_MAC)
        return self._port_macs

    def _connect(self, client=None):
        self.client.connect(self.vnfd_helper)

    def get_stats(self, *args, **kwargs):
        return self.client.get_statistics()

    def stop_collect(self):
        self._terminated.value = 1

    def generate_samples(self, ports, key=None):
        stats = self.get_stats()

        samples = {}
        # this is not DPDK port num, but this is whatever number we gave
        # when we selected ports and programmed the profile
        for port_num in ports:
            try:
                # reverse lookup port name from port_num so the stats dict is descriptive
                intf = self.vnfd_helper.find_interface_by_port(port_num)
                port_name = intf["name"]
                samples[port_name] = {
                    "rx_throughput_kps": float(stats["Rx_Rate_Kbps"][port_num]),
                    "tx_throughput_kps": float(stats["Tx_Rate_Kbps"][port_num]),
                    "rx_throughput_mbps": float(stats["Rx_Rate_Mbps"][port_num]),
                    "tx_throughput_mbps": float(stats["Tx_Rate_Mbps"][port_num]),
                    "in_packets": int(stats["Valid_Frames_Rx"][port_num]),
                    "out_packets": int(stats["Frames_Tx"][port_num]),
                    # NOTE(ralonsoh): we need to make the traffic injection
                    # time variable.
                    "RxThroughput": int(stats["Valid_Frames_Rx"][port_num]) / 30,
                    "TxThroughput": int(stats["Frames_Tx"][port_num]) / 30,
                }
                if key:
                    avg_latency = stats["Store-Forward_Avg_latency_ns"][port_num]
                    min_latency = stats["Store-Forward_Min_latency_ns"][port_num]
                    max_latency = stats["Store-Forward_Max_latency_ns"][port_num]
                    samples[port_name][key] = \
                        {"Store-Forward_Avg_latency_ns": avg_latency,
                         "Store-Forward_Min_latency_ns": min_latency,
                         "Store-Forward_Max_latency_ns": max_latency}
            except IndexError:
                pass

        return samples

    def _initialize_client(self):
        """Initialize the IXIA IxNetwork client and configure the server"""
        self.client.clear_config()
        self.client.assign_ports()
        self.client.create_traffic_model()

    def run_one_injection(self, traffic_profile, mq_producer):
        self._build_ports()
        self._initialize_client()
        min_tol = self.rfc_helper.tolerance_low
        max_tol = self.rfc_helper.tolerance_high
        try:
            first_run = traffic_profile.execute_traffic(
                self, self.client, self.port_macs)
            self.client_started.value = 1
            # pylint: disable=unnecessary-lambda
            utils.wait_until_true(lambda: self.client.is_traffic_stopped())
            mq_producer.tg_method_iteration(self._iteration_index)
            samples = self.generate_samples(traffic_profile.ports)
            completed, samples = traffic_profile.get_drop_percentage(
                samples, min_tol, max_tol, first_run=first_run)
            self._queue.put(samples)
            return completed
        except Exception:  # pylint: disable=broad-except
            LOG.exception('Run Traffic terminated')
            return True

    def run_traffic(self, traffic_profile, mq_producer):
        mq_producer.tg_method_started()
        if traffic_profile.mq_enabled:
            return
        while self._terminated.value == 0:
            if self.run_one_injection(traffic_profile, mq_producer):
                self._terminated.value = 1
        mq_producer.tg_method_finished()

    def collect_kpi(self):
        self.rfc_helper.iteration.value += 1
        return super(IxiaResourceHelper, self).collect_kpi()


class IxiaTrafficGen(sample_vnf.SampleVNFTrafficGen,
                     vnf_base.GenericVNFEndpoint):

    APP_NAME = 'Ixia'

    def __init__(self, name, vnfd, task_id, setup_env_helper_type=None,
                 resource_helper_type=None):
        resource_helper_type = (IxiaResourceHelper if resource_helper_type
                                is None else resource_helper_type)
        sample_vnf.SampleVNFTrafficGen.__init__(
            self, name, vnfd, task_id, setup_env_helper_type,
            resource_helper_type)
        self._ixia_traffic_gen = None
        self.ixia_file_name = ''
        self.vnf_port_pairs = []
        self._traffic_profile = None

        self.queue = multiprocessing.Queue()
        self._id = uuid.uuid1().int
        vnf_base.GenericVNFEndpoint.__init__(self, self._id, [task_id],
                                             self.queue)
        self._mq_consumer = vnf_base.GenericVNFConsumer([task_id], self)
        ###self._mq_consumer.start_rpc_server()

    def _check_status(self):
        pass

    def terminate(self):
        self.resource_helper.stop_collect()
        super(IxiaTrafficGen, self).terminate()

    def runner_method_start_iteration(self, ctxt, **kwargs):
        if ctxt['id'] in self._ctx_ids:
            self.resource_helper.run_one_injection(self._traffic_profile,
                                                   self._mq_producer)

    def runner_method_stop_iteration(self, ctxt, **kwargs):
        pass
