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
import yaml
import os
from functools import partial
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


class HelperFunc(object):
    """ Helper to include all the common code """
    def __init__(self):
        super(HelperFunc, self).__init__()

    def generate_port_pairs(self, topology_file):
        """ Function to read the toplogy and get tg & vnf port list """
        with open(topology_file) as fh:
            yaml_data = yaml.safe_load(fh.read())
        tg_port_pairs = []
        vnf_port_pairs = []
        for ele in yaml_data['nsd:nsd-catalog']['nsd'][0]['vld']:
            if ele['id'].startswith('private'):
                private_id = ele['id']
                private_data = ele['vnfd-connection-point-ref']
                public_id = 'public' if private_id == \
                    'private' else 'public_' + private_id.split('_')[1]
                public_data = [ele['vnfd-connection-point-ref'] for
                               ele in yaml_data[
                                   'nsd:nsd-catalog']['nsd'][0]['vld'] if
                               ele['id'] == public_id][0]
                vnf_id_ref = private_data[1]['member-vnf-index-ref']
                tg_1_id_ref = private_data[0]['member-vnf-index-ref']
                tg_2_id_ref = public_data[1]['member-vnf-index-ref']
                private_data.extend(public_data)
                port_pair = tuple(data[
                    'vnfd-connection-point-ref'] for data in private_data if
                    data['member-vnf-index-ref'] == vnf_id_ref)
                vnf_port_pairs.append(port_pair)
                tg_port_pair = tuple(data[
                    'vnfd-connection-point-ref'] for data in private_data if
                    data['member-vnf-index-ref'] in (tg_1_id_ref, tg_2_id_ref))
                tg_port_pairs.append(tg_port_pair)
        return [tg_port_pairs, vnf_port_pairs]


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
        self.name = "vnf__1"  # name in topology file
        self.bin_path = get_nsb_option("bin_path", "")
        self.helperfunc = HelperFunc()
        self.rel_bin_path = partial(os.path.join, self.bin_path)

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

    def _update_config_file(self, ip_pipeline_cfg, mcpi, vnf_type):
        pipeline_config_str = ip_pipeline_cfg
        for i in range(len(mcpi)):
            find_str = mcpi[i].split('=')
            if find_str[1] != '':
                where = pipeline_config_str.find(find_str[0])
                if where != -1:
                    l = pipeline_config_str[:where]
                    r = pipeline_config_str[where:]
                    tmp = r.find('\n')
                    r = r[tmp:]
                    cmd = find_str[0] + '= ' + find_str[1]
                    cmd += '\n'
                    pipeline_config_str = l + cmd + r
                else:
                    where = pipeline_config_str.find('type ' + '= ' + vnf_type)
                    l = pipeline_config_str[:where]
                    r = pipeline_config_str[where:]
                    tmp = r.find('\n')
                    r = r[tmp:]
                    cmd_1 = "type =" + " " + vnf_type
                    cmd_1 += '\n'
                    cmd_2 = find_str[0] + '= ' + find_str[1]
                    cmd_2 += '\n'
                    pipeline_config_str = l + cmd_1 + cmd_2 + r

            elif find_str[1] == '':
                where = pipeline_config_str.find(find_str[0])
                l = pipeline_config_str[:where]
                r = pipeline_config_str[where:]
                tmp = r.find('\n')
                r = r[tmp:]
                cmd = ''
                cmd += '\n'
                pipeline_config_str = l + cmd + r

        return pipeline_config_str

    def _update_traffic_type(self, ip_pipeline_cfg, traffic_options):
        if traffic_options['vnf_type'] is not 'CGNAT':
            pipeline_config_str = ip_pipeline_cfg.replace(
                'traffic_type = 4', 'traffic_type = ' + str(
                    traffic_options['traffic_type']))
        else:
            t_type = 'IPv4'
            if traffic_options['traffic_type'] is 4:
                t_type = 'ipv4'
            else:
                t_type = 'ipv6'
            pipeline_config_str = ip_pipeline_cfg.replace(
                'pkt_type = ipv4', 'pkt_type = ' + t_type)

        return pipeline_config_str

    def _update_packet_type(self, ip_pipeline_cfg, traffic_options):
        pipeline_config_str = ip_pipeline_cfg.replace(
            'pkt_type = ipv4', 'pkt_type = ' + traffic_options['pkt_type'])

        return pipeline_config_str

    def _update_fw_script_file(self, ip_pipeline_cfg, mcpi, vnf_str):

        pipeline_config_str = ip_pipeline_cfg
        input_cmds = ''
        for i in range(len(mcpi)):
            input_cmds += mcpi[i]
            input_cmds += '\n'
        for i in range(len(mcpi)):
            where = pipeline_config_str.find(vnf_str)
            l = pipeline_config_str[:where]
            r = pipeline_config_str[where:]
            tmp = r.find('\n')
            r = r[tmp:]
            cmd_1 = vnf_str
            cmd_1 += '\n'
            pipeline_config_str = l + cmd_1 + input_cmds + r
            break

        return pipeline_config_str

    def _update_cgnat_script_file(self, ip_pipeline_cfg, mcpi, vnf_str):

        pipeline_config_str = ip_pipeline_cfg
        input_cmds = ''
        icmp_flag = False
        for i in range(len(mcpi)):
            if mcpi[i] == 'link 0 down':
                icmp_flag = True
            input_cmds += mcpi[i]
            input_cmds += '\n'
        if icmp_flag is True:
            return '\n' + input_cmds
        else:
            return pipeline_config_str + '\n' + input_cmds


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

    def generate_port_pairs(self, topology_file):
        self.tg_port_pairs, self.vnf_port_pairs = \
            self.helperfunc.generate_port_pairs(topology_file)


class GenericTrafficGen(GenericVNF):
    """ Class providing file-like API for generic traffic generator """

    def __init__(self, vnfd):
        super(GenericTrafficGen, self).__init__(vnfd)
        self.runs_traffic = True
        self.traffic_finished = False
        self.name = "tgen__1"  # name in topology file

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

    def generate_port_pairs(self, topology_file):
        self.tg_port_pairs, self.vnf_port_pairs = \
            self.helperfunc.generate_port_pairs(topology_file)
