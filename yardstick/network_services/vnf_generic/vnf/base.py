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
import ipaddress
import six

from yardstick.network_services.utils import get_nsb_option

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


class GenericVNF(object):
    """ Class providing file-like API for generic VNF implementation """
    def __init__(self, vnfd):
        super(GenericVNF, self).__init__()
        self.vnfd = vnfd  # fixme: parse this into a structure
        # List of statistics we can obtain from this VNF
        # - ETSI MANO 6.3.1.1 monitoring_parameter
        self.kpi = self._get_kpi_definition(vnfd)
        # Standard dictionary containing params like thread no, buffer size etc
        self.config = {}
        self.runs_traffic = False
        # overwritten by load_vnf_model
        self.name = ""  # name in topology file
        self.bin_path = get_nsb_option("bin_path", "")

    @classmethod
    def _get_kpi_definition(cls, vnfd):
        """ Get list of KPIs defined in VNFD

        :param vnfd:
        :return: list of KPIs, e.g. ['throughput', 'latency']
        """
        return vnfd['benchmark']['kpi']

    @classmethod
    def get_ip_version(cls, ip_addr):
        """ get ip address version v6 or v4 """
        try:
            address = ipaddress.ip_address(six.text_type(ip_addr))
        except ValueError:
            LOG.error(ip_addr, " is not valid")
            return
        else:
            return address.version

    def _ip_to_hex(self, ip_addr):
        ip_to_convert = ip_addr.split(".")
        ip_x = ip_addr
        if self.get_ip_version(ip_addr) == 4:
            ip_to_convert = ip_addr.split(".")
            ip_octect = [int(octect) for octect in ip_to_convert]
            ip_x = "{0[0]:02X}{0[1]:02X}{0[2]:02X}{0[3]:02X}".format(ip_octect)
        return ip_x

    def _get_dpdk_port_num(self, name):
        for intf in self.vnfd['vdu'][0]['external-interface']:
            if name == intf['name']:
                return intf['virtual-interface']['dpdk_port_num']

    def _append_routes(self, ip_pipeline_cfg):
        if 'routing_table' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['routing_table']

            where = ip_pipeline_cfg.find("arp_route_tbl")
            link = ip_pipeline_cfg[:where]
            route_add = ip_pipeline_cfg[where:]

            tmp = route_add.find('\n')
            route_add = route_add[tmp:]

            cmds = "arp_route_tbl ="

            for route in routing_table:
                net = self._ip_to_hex(route['network'])
                net_nm = self._ip_to_hex(route['netmask'])
                net_gw = self._ip_to_hex(route['gateway'])
                port = self._get_dpdk_port_num(route['if'])
                cmd = \
                    " ({port0_local_ip_hex},{port0_netmask_hex},{dpdk_port},"\
                    "{port1_local_ip_hex})".format(port0_local_ip_hex=net,
                                                   port0_netmask_hex=net_nm,
                                                   dpdk_port=port,
                                                   port1_local_ip_hex=net_gw)
                cmds += cmd

            cmds += '\n'
            ip_pipeline_cfg = link + cmds + route_add

        return ip_pipeline_cfg

    def _append_nd_routes(self, ip_pipeline_cfg):
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            where = ip_pipeline_cfg.find("nd_route_tbl")
            link = ip_pipeline_cfg[:where]
            route_nd = ip_pipeline_cfg[where:]

            tmp = route_nd.find('\n')
            route_nd = route_nd[tmp:]

            cmds = "nd_route_tbl ="

            for route in routing_table:
                net = route['network']
                net_nm = route['netmask']
                net_gw = route['gateway']
                port = self._get_dpdk_port_num(route['if'])
                cmd = \
                    " ({port0_local_ip_hex},{port0_netmask_hex},{dpdk_port},"\
                    "{port1_local_ip_hex})".format(port0_local_ip_hex=net,
                                                   port0_netmask_hex=net_nm,
                                                   dpdk_port=port,
                                                   port1_local_ip_hex=net_gw)
                cmds += cmd

            cmds += '\n'
            ip_pipeline_cfg = link + cmds + route_nd

        return ip_pipeline_cfg

    def _get_port0localip6(self):
        return_value = ""
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            inc = 0
            for route in routing_table:
                inc += 1
                if inc == 1:
                    return_value = route['network']
        LOG.info("_get_port0localip6 : %s", return_value)
        return return_value

    def _get_port1localip6(self):
        return_value = ""
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            inc = 0
            for route in routing_table:
                inc += 1
                if inc == 2:
                    return_value = route['network']
        LOG.info("_get_port1localip6 : %s", return_value)
        return return_value

    def _get_port0prefixlen6(self):
        return_value = ""
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            inc = 0
            for route in routing_table:
                inc += 1
                if inc == 1:
                    return_value = route['netmask']
        LOG.info("_get_port0prefixlen6 : %s", return_value)
        return return_value

    def _get_port1prefixlen6(self):
        return_value = ""
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            inc = 0
            for route in routing_table:
                inc += 1
                if inc == 2:
                    return_value = route['netmask']
        LOG.info("_get_port1prefixlen6 : %s", return_value)
        return return_value

    def _get_port0gateway6(self):
        return_value = ""
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            inc = 0
            for route in routing_table:
                inc += 1
                if inc == 1:
                    return_value = route['network']
        LOG.info("_get_port0gateway6 : %s", return_value)
        return return_value

    def _get_port1gateway6(self):
        return_value = ""
        if 'nd_route_tbl' in self.vnfd['vdu'][0]:
            routing_table = self.vnfd['vdu'][0]['nd_route_tbl']

            inc = 0
            for route in routing_table:
                inc += 1
                if inc == 2:
                    return_value = route['network']
        LOG.info("_get_port1gateway6 : %s", return_value)
        return return_value

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

    @classmethod
    def setup_hugepages(cls, connection):
        hugepages = \
            connection.execute(
                "awk '/Hugepagesize/ { print $2$3 }' < /proc/meminfo")[1]
        hugepages = hugepages.rstrip()

        memory_path = \
            '/sys/kernel/mm/hugepages/hugepages-%s/nr_hugepages' % hugepages
        connection.execute("awk -F: '{ print $1 }' < %s" % memory_path)

        pages = 16384 if hugepages.rstrip() == "2048kB" else 16
        connection.execute("echo %s | sudo tee %s" % (pages, memory_path))


class GenericTrafficGen(GenericVNF):
    """ Class providing file-like API for generic traffic generator """

    def __init__(self, vnfd):
        super(GenericTrafficGen, self).__init__(vnfd)
        self.runs_traffic = True
        self.traffic_finished = False
        self.name = ""  # name in topology file

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
