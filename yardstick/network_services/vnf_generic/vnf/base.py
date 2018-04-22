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
""" Base class implementation for generic vnf implementation """

import abc

import logging
import six

from yardstick.common import messaging
from yardstick.common.messaging import payloads
from yardstick.common.messaging import producer
from yardstick.network_services.helpers.samplevnf_helper import PortPairs


LOG = logging.getLogger(__name__)


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


class VnfdHelper(dict):

    def __init__(self, *args, **kwargs):
        super(VnfdHelper, self).__init__(*args, **kwargs)
        self.port_pairs = PortPairs(self['vdu'][0]['external-interface'])
        # port num is not present until binding so we have to memoize
        self._port_num_map = {}

    @property
    def mgmt_interface(self):
        return self["mgmt-interface"]

    @property
    def vdu(self):
        return self['vdu']

    @property
    def vdu0(self):
        return self.vdu[0]

    @property
    def interfaces(self):
        return self.vdu0['external-interface']

    @property
    def kpi(self):
        return self['benchmark']['kpi']

    def find_virtual_interface(self, **kwargs):
        key, value = next(iter(kwargs.items()))
        for interface in self.interfaces:
            virtual_intf = interface["virtual-interface"]
            if virtual_intf[key] == value:
                return interface
        raise KeyError()

    def find_interface(self, **kwargs):
        key, value = next(iter(kwargs.items()))
        for interface in self.interfaces:
            if interface[key] == value:
                return interface
        raise KeyError()

    # hide dpdk_port_num key so we can abstract
    def find_interface_by_port(self, port):
        for interface in self.interfaces:
            virtual_intf = interface["virtual-interface"]
            # we have to convert to int to compare
            if int(virtual_intf['dpdk_port_num']) == port:
                return interface
        raise KeyError()

    def port_num(self, port):
        # we need interface name -> DPDK port num (PMD ID) -> LINK ID
        # LINK ID -> PMD ID is governed by the port mask
        """

        :rtype: int
        :type port: str
        """
        if isinstance(port, dict):
            intf = port
        else:
            intf = self.find_interface(name=port)
        return self._port_num_map.setdefault(intf["name"],
                                             int(intf["virtual-interface"]["dpdk_port_num"]))

    def port_nums(self, intfs):
        return [self.port_num(i) for i in intfs]

    def ports_iter(self):
        for port_name in self.port_pairs.all_ports:
            port_num = self.port_num(port_name)
            yield port_name, port_num


class TrafficGeneratorProducer(producer.MessagingProducer):
    """Class implementing the message producer for traffic generators

    This message producer must be instantiated in the process created
    "run_traffic" process.
    """
    def __init__(self, pid):
        super(TrafficGeneratorProducer, self).__init__(messaging.TOPIC_TG,
                                                       pid=pid)


@six.add_metaclass(abc.ABCMeta)
class GenericVNF(object):
    """Class providing file-like API for generic VNF implementation

    Currently the only class implementing this interface is
    yardstick/network_services/vnf_generic/vnf/sample_vnf:SampleVNF.
    """

    # centralize network naming convention
    UPLINK = PortPairs.UPLINK
    DOWNLINK = PortPairs.DOWNLINK

    def __init__(self, name, vnfd):
        self.name = name
        self.vnfd_helper = VnfdHelper(vnfd)
        # List of statistics we can obtain from this VNF
        # - ETSI MANO 6.3.1.1 monitoring_parameter
        self.kpi = self.vnfd_helper.kpi
        # Standard dictionary containing params like thread no, buffer size etc
        self.config = {}
        self.runs_traffic = False

    @abc.abstractmethod
    def instantiate(self, scenario_cfg, context_cfg):
        """Prepare VNF for operation and start the VNF process/VM

        :param scenario_cfg: Scenario config
        :param context_cfg: Context config
        :return: True/False
        """

    @abc.abstractmethod
    def wait_for_instantiate(self):
        """Wait for VNF to start

        :return: True/False
        """

    @abc.abstractmethod
    def terminate(self):
        """Kill all VNF processes"""

    @abc.abstractmethod
    def scale(self, flavor=""):
        """rest

        :param flavor: Name of the flavor.
        :return:
        """

    @abc.abstractmethod
    def collect_kpi(self):
        """Return a dict containing the selected KPI at a given point of time

        :return: {"kpi": value, "kpi2": value}
        """


@six.add_metaclass(abc.ABCMeta)
class GenericTrafficGen(GenericVNF):
    """ Class providing file-like API for generic traffic generator """

    def __init__(self, name, vnfd):
        super(GenericTrafficGen, self).__init__(name, vnfd)
        self.runs_traffic = True
        self.traffic_finished = False
        self._mq_producer = None

    @abc.abstractmethod
    def run_traffic(self, traffic_profile):
        """Generate traffic on the wire according to the given params.

        This method is non-blocking, returns immediately when traffic process
        is running. Mandatory.

        :param traffic_profile:
        :return: True/False
        """

    @abc.abstractmethod
    def terminate(self):
        """After this method finishes, all traffic processes should stop.

        Mandatory.

        :return: True/False
        """

    def listen_traffic(self, traffic_profile):
        """Listen to traffic with the given parameters.

        Method is non-blocking, returns immediately when traffic process
        is running. Optional.

        :param traffic_profile:
        :return: True/False
        """
        pass

    def verify_traffic(self, traffic_profile):
        """Verify captured traffic after it has ended.

        Optional.

        :param traffic_profile:
        :return: dict
        """
        pass

    def wait_for_instantiate(self):
        """Wait for an instance to load.

        Optional.

        :return: True/False
        """
        pass

    def _setup_mq_producer(self, pid):
        """Setup the TG MQ producer to send messages between processes

        :return: (derived class from ``MessagingProducer``) MQ producer object
        """
        return TrafficGeneratorProducer(pid)
