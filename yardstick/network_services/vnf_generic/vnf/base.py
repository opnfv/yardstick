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

from __future__ import absolute_import
import logging

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

    def find_interface(self, **kwargs):
        key, value = next(iter(kwargs.items()))
        for interface in self.interfaces:
            if interface[key] == value:
                return interface


class VNFObject(object):

    def __init__(self, name, vnfd):
        super(VNFObject, self).__init__()
        self.name = name
        self.vnfd_helper = VnfdHelper(vnfd)  # fixme: parse this into a structure


class GenericVNF(VNFObject):

    """ Class providing file-like API for generic VNF implementation """
    def __init__(self, name, vnfd):
        super(GenericVNF, self).__init__(name, vnfd)
        # List of statistics we can obtain from this VNF
        # - ETSI MANO 6.3.1.1 monitoring_parameter
        self.kpi = self._get_kpi_definition()
        # Standard dictionary containing params like thread no, buffer size etc
        self.config = {}
        self.runs_traffic = False

    def _get_kpi_definition(self):
        """ Get list of KPIs defined in VNFD

        :param vnfd:
        :return: list of KPIs, e.g. ['throughput', 'latency']
        """
        return self.vnfd_helper.kpi

    def instantiate(self, scenario_cfg, context_cfg):
        """ Prepare VNF for operation and start the VNF process/VM

        :param scenario_cfg:
        :param context_cfg:
        :return: True/False
        """
        raise NotImplementedError()

    def terminate(self):
        """ Kill all VNF processes

        :return:
        """
        raise NotImplementedError()

    def scale(self, flavor=""):
        """

        :param flavor:
        :return:
        """
        raise NotImplementedError()

    def collect_kpi(self):
        """This method should return a dictionary containing the
        selected KPI at a given point of time.

        :return: {"kpi": value, "kpi2": value}
        """
        raise NotImplementedError()


class GenericTrafficGen(GenericVNF):
    """ Class providing file-like API for generic traffic generator """

    def __init__(self, name, vnfd):
        super(GenericTrafficGen, self).__init__(name, vnfd)
        self.runs_traffic = True
        self.traffic_finished = False

    def run_traffic(self, traffic_profile):
        """ Generate traffic on the wire according to the given params.
        Method is non-blocking, returns immediately when traffic process
        is running. Mandatory.

        :param traffic_profile:
        :return: True/False
        """
        raise NotImplementedError()

    def listen_traffic(self, traffic_profile):
        """ Listen to traffic with the given parameters.
        Method is non-blocking, returns immediately when traffic process
        is running. Optional.

        :param traffic_profile:
        :return: True/False
        """
        pass

    def verify_traffic(self, traffic_profile):
        """ Verify captured traffic after it has ended. Optional.

        :param traffic_profile:
        :return: dict
        """
        pass

    def terminate(self):
        """ After this method finishes, all traffic processes should stop. Mandatory.

        :return: True/False
        """
        raise NotImplementedError()
