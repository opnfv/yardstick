##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
from __future__ import print_function

import collections
import logging
import os
# because we need to mock only this one
from os.path import exists
import errno
from collections import OrderedDict

import ipaddress
import pkg_resources

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.model import Network
from yardstick.benchmark.contexts.model import PlacementGroup, ServerGroup
from yardstick.benchmark.contexts.model import Server
from yardstick.benchmark.contexts.model import update_scheduler_hints
from yardstick.common import exceptions as y_exc
from yardstick.common.openstack_utils import get_shade_client
from yardstick.orchestrator.heat import HeatStack
from yardstick.orchestrator.heat import HeatTemplate
from yardstick.common import constants as consts
from yardstick.common import utils
from yardstick.common.utils import source_env
from yardstick.ssh import SSH

LOG = logging.getLogger(__name__)

DEFAULT_HEAT_TIMEOUT = 3600


def join_args(sep, *args):
    return sep.join(args)


def h_join(*args):
    return '-'.join(args)


class HeatContext(Context):
    """Class that represents a context in the logical model"""

    __context_type__ = "Heat"

    def __init__(self):
        self.stack = None
        self.networks = OrderedDict()
        self.heat_timeout = None
        self.servers = []
        self.placement_groups = []
        self.server_groups = []
        self.keypair_name = None
        self.secgroup_name = None
        self._server_map = {}
        self.attrs = {}
        self._image = None
        self._flavor = None
        self.flavors = set()
        self._user = None
        self.template_file = None
        self.heat_parameters = None
        self.shade_client = None
        self.heat_timeout = None
        self.key_filename = None
        super(HeatContext, self).__init__()

    @staticmethod
    def assign_external_network(networks):
        sorted_networks = sorted(networks.items())
        external_network = os.environ.get("EXTERNAL_NETWORK", "net04_ext")

        have_external_network = any(net.get("external_network") for net in networks.values())
        if not have_external_network:
            # try looking for mgmt network first
            try:
                networks['mgmt']["external_network"] = external_network
            except KeyError:
                if sorted_networks:
                    # otherwise assign it to first network using os.environ
                    sorted_networks[0][1]["external_network"] = external_network

        return sorted_networks

    def init(self, attrs):
        """Initializes itself from the supplied arguments"""
        super(HeatContext, self).init(attrs)

        self.check_environment()
        self._user = attrs.get("user")

        self.template_file = attrs.get("heat_template")

        self.heat_timeout = attrs.get("timeout", DEFAULT_HEAT_TIMEOUT)
        if self.template_file:
            self.heat_parameters = attrs.get("heat_parameters")
            return

        self.keypair_name = h_join(self.name, "key")
        self.secgroup_name = h_join(self.name, "secgroup")

        self._image = attrs.get("image")

        self._flavor = attrs.get("flavor")

        self.placement_groups = [PlacementGroup(name, self, pg_attrs["policy"])
                                 for name, pg_attrs in attrs.get(
                                 "placement_groups", {}).items()]

        self.server_groups = [ServerGroup(name, self, sg_attrs["policy"])
                              for name, sg_attrs in attrs.get(
                              "server_groups", {}).items()]

        # we have to do this first, because we are injecting external_network
        # into the dict
        sorted_networks = self.assign_external_network(attrs["networks"])

        self.networks = OrderedDict(
            (name, Network(name, self, net_attrs)) for name, net_attrs in
            sorted_networks)

        for name, server_attrs in sorted(attrs["servers"].items()):
            server = Server(name, self, server_attrs)
            self.servers.append(server)
            self._server_map[server.dn] = server

        self.attrs = attrs

    def check_environment(self):
        try:
            os.environ['OS_AUTH_URL']
        except KeyError:
            try:
                source_env(consts.OPENRC)
            except IOError as e:
                if e.errno != errno.EEXIST:
                    LOG.error('OPENRC file not found')
                    raise
                else:
                    LOG.error('OS_AUTH_URL not found')

    @property
    def image(self):
        """returns application's default image name"""
        return self._image

    @property
    def flavor(self):
        """returns application's default flavor name"""
        return self._flavor

    @property
    def user(self):
        """return login user name corresponding to image"""
        return self._user

    def _add_resources_to_template(self, template):
        """add to the template the resources represented by this context"""

        if self.flavor:
            if isinstance(self.flavor, dict):
                flavor = self.flavor.setdefault("name", self.name + "-flavor")
                template.add_flavor(**self.flavor)
                self.flavors.add(flavor)

        template.add_keypair(self.keypair_name, self.name)
        template.add_security_group(self.secgroup_name)

        for network in self.networks.values():
            # Using existing network
            if network.is_existing():
                continue
            template.add_network(network.stack_name,
                                 network.physical_network,
                                 network.provider,
                                 network.segmentation_id,
                                 network.port_security_enabled,
                                 network.network_type)
            template.add_subnet(network.subnet_stack_name, network.stack_name,
                                network.subnet_cidr,
                                network.enable_dhcp,
                                network.gateway_ip)

            if network.router:
                template.add_router(network.router.stack_name,
                                    network.router.external_gateway_info,
                                    network.subnet_stack_name)
                template.add_router_interface(network.router.stack_if_name,
                                              network.router.stack_name,
                                              network.subnet_stack_name)

        # create a list of servers sorted by increasing no of placement groups
        list_of_servers = sorted(self.servers,
                                 key=lambda s: len(s.placement_groups))

        #
        # add servers with scheduler hints derived from placement groups
        #

        # create list of servers with availability policy
        availability_servers = []
        for server in list_of_servers:
            for pg in server.placement_groups:
                if pg.policy == "availability":
                    availability_servers.append(server)
                    break

        for server in availability_servers:
            if isinstance(server.flavor, dict):
                try:
                    self.flavors.add(server.flavor["name"])
                except KeyError:
                    self.flavors.add(h_join(server.stack_name, "flavor"))

        # add servers with availability policy
        added_servers = []
        for server in availability_servers:
            scheduler_hints = {}
            for pg in server.placement_groups:
                update_scheduler_hints(scheduler_hints, added_servers, pg)
            # workaround for openstack nova bug, check JIRA: YARDSTICK-200
            # for details
            if len(availability_servers) == 2:
                if not scheduler_hints["different_host"]:
                    scheduler_hints.pop("different_host", None)
                    server.add_to_template(template,
                                           list(self.networks.values()),
                                           scheduler_hints)
                else:
                    scheduler_hints["different_host"] = \
                        scheduler_hints["different_host"][0]
                    server.add_to_template(template,
                                           list(self.networks.values()),
                                           scheduler_hints)
            else:
                server.add_to_template(template,
                                       list(self.networks.values()),
                                       scheduler_hints)
            added_servers.append(server.stack_name)

        # create list of servers with affinity policy
        affinity_servers = []
        for server in list_of_servers:
            for pg in server.placement_groups:
                if pg.policy == "affinity":
                    affinity_servers.append(server)
                    break

        # add servers with affinity policy
        for server in affinity_servers:
            if server.stack_name in added_servers:
                continue
            scheduler_hints = {}
            for pg in server.placement_groups:
                update_scheduler_hints(scheduler_hints, added_servers, pg)
            server.add_to_template(template, list(self.networks.values()),
                                   scheduler_hints)
            added_servers.append(server.stack_name)

        # add server group
        for sg in self.server_groups:
            template.add_server_group(sg.name, sg.policy)

        # add remaining servers with no placement group configured
        for server in list_of_servers:
            # TODO placement_group and server_group should combine
            if not server.placement_groups:
                scheduler_hints = {}
                # affinity/anti-aff server group
                sg = server.server_group
                if sg:
                    scheduler_hints["group"] = {'get_resource': sg.name}
                server.add_to_template(template,
                                       list(self.networks.values()),
                                       scheduler_hints)

    def get_neutron_info(self):
        if not self.shade_client:
            self.shade_client = get_shade_client()

        networks = self.shade_client.list_networks()
        for network in self.networks.values():
            for neutron_net in (net for net in networks if net.name == network.stack_name):
                    network.segmentation_id = neutron_net.get('provider:segmentation_id')
                    # we already have physical_network
                    # network.physical_network = neutron_net.get('provider:physical_network')
                    network.network_type = neutron_net.get('provider:network_type')
                    network.neutron_info = neutron_net

    def _create_new_stack(self, heat_template):
         try:
             return heat_template.create(block=True,
                                         timeout=self.heat_timeout)
         except KeyboardInterrupt:
             raise y_exc.StackCreationInterrupt
         except Exception:
             LOG.exception("stack failed")
             # let the other failures happen, we want stack trace
             raise

    def _retrieve_existing_stack(self, stack_name):
        stack = HeatStack(stack_name)
        if stack.get():
            return stack
        else:
            LOG.warning("Stack %s does not exist", self.name)
            return None

    def deploy(self):
        """deploys template into a stack using cloud"""
        LOG.info("Deploying context '%s' START", self.name)

        self.key_filename = ''.join(
            [consts.YARDSTICK_ROOT_PATH,
             'yardstick/resources/files/yardstick_key-',
             self.name])
        # Permissions may have changed since creation; this can be fixed. If we
        # overwrite the file, we lose future access to VMs using this key.
        # As long as the file exists, even if it is unreadable, keep it intact
        if not exists(self.key_filename):
            SSH.gen_keys(self.key_filename)

        heat_template = HeatTemplate(self.name, self.template_file,
                                     self.heat_parameters)

        if self.template_file is None:
            self._add_resources_to_template(heat_template)

        if self._flags.no_setup:
            # Try to get an existing stack, returns a stack or None
            self.stack = self._retrieve_existing_stack(self.name)
            if not self.stack:
                self.stack = self._create_new_stack(heat_template)

        else:
            self.stack = self._create_new_stack(heat_template)

        # TODO: use Neutron to get segmentation-id
        self.get_neutron_info()

        # copy some vital stack output into server objects
        for server in self.servers:
            if server.ports:
                self.add_server_port(server)

            if server.floating_ip:
                server.public_ip = \
                    self.stack.outputs[server.floating_ip["stack_name"]]

        LOG.info("Deploying context '%s' DONE", self.name)

    @staticmethod
    def _port_net_is_existing(port_info):
        net_flags = port_info.get('net_flags', {})
        return net_flags.get(consts.IS_EXISTING)

    @staticmethod
    def _port_net_is_public(port_info):
        net_flags = port_info.get('net_flags', {})
        return net_flags.get(consts.IS_PUBLIC)

    def add_server_port(self, server):
        server_ports = server.ports.values()
        for server_port in server_ports:
            port_info = server_port[0]
            port_ip = self.stack.outputs[port_info["stack_name"]]
            port_net_is_existing = self._port_net_is_existing(port_info)
            port_net_is_public = self._port_net_is_public(port_info)
            if port_net_is_existing and (port_net_is_public or
                                         len(server_ports) == 1):
                server.public_ip = port_ip
            if not server.private_ip or len(server_ports) == 1:
                server.private_ip = port_ip

        server.interfaces = {}
        for network_name, ports in server.ports.items():
            for port in ports:
                # port['port'] is either port name from mapping or default network_name
                if self._port_net_is_existing(port):
                    continue
                server.interfaces[port['port']] = self.make_interface_dict(network_name,
                                                                           port['port'],
                                                                           port['stack_name'],
                                                                           self.stack.outputs)
                server.override_ip(network_name, port)

    def make_interface_dict(self, network_name, port, stack_name, outputs):
        private_ip = outputs[stack_name]
        mac_address = outputs[h_join(stack_name, "mac_address")]
        # these are attributes of the network, not the port
        output_subnet_cidr = outputs[h_join(self.name, network_name,
                                            'subnet', 'cidr')]

        # these are attributes of the network, not the port
        output_subnet_gateway = outputs[h_join(self.name, network_name,
                                               'subnet', 'gateway_ip')]

        return {
            # add default port name
            "name": port,
            "private_ip": private_ip,
            "subnet_id": outputs[h_join(stack_name, "subnet_id")],
            "subnet_cidr": output_subnet_cidr,
            "network": str(ipaddress.ip_network(output_subnet_cidr).network_address),
            "netmask": str(ipaddress.ip_network(output_subnet_cidr).netmask),
            "gateway_ip": output_subnet_gateway,
            "mac_address": mac_address,
            "device_id": outputs[h_join(stack_name, "device_id")],
            "network_id": outputs[h_join(stack_name, "network_id")],
            # this should be == vld_id for NSB tests
            "network_name": network_name,
            # to match vnf_generic
            "local_mac": mac_address,
            "local_ip": private_ip,
        }

    def _delete_key_file(self):
        try:
            utils.remove_file(self.key_filename)
            utils.remove_file(self.key_filename + ".pub")
        except OSError:
            LOG.exception("There was an error removing the key file %s",
                          self.key_filename)

    def undeploy(self):
        """undeploys stack from cloud"""
        if self._flags.no_teardown:
            LOG.info("Undeploying context '%s' SKIP", self.name)
            return

        if self.stack:
            LOG.info("Undeploying context '%s' START", self.name)
            self.stack.delete()
            self.stack = None
            LOG.info("Undeploying context '%s' DONE", self.name)

            self._delete_key_file()

        super(HeatContext, self).undeploy()

    @staticmethod
    def generate_routing_table(server):
        routes = [
            {
                "network": intf["network"],
                "netmask": intf["netmask"],
                "if": name,
                # We have to encode a None gateway as '' for Jinja2 to YAML conversion
                "gateway": intf["gateway_ip"] if intf["gateway_ip"] else '',
            }
            for name, intf in server.interfaces.items()
        ]
        return routes

    def _get_server(self, attr_name):
        """lookup server info by name from context
        attr_name: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        """
        if isinstance(attr_name, collections.Mapping):
            node_name, cname = self.split_name(attr_name['name'])
            if cname is None or cname != self.name:
                return None

            # Create a dummy server instance for holding the *_ip attributes
            server = Server(node_name, self, {})
            server.public_ip = self.stack.outputs.get(
                attr_name.get("public_ip_attr", object()), None)

            server.private_ip = self.stack.outputs.get(
                attr_name.get("private_ip_attr", object()), None)
        else:
            try:
                server = self._server_map[attr_name]
            except KeyError:
                attr_name_no_suffix = attr_name.split("-")[0]
                server = self._server_map.get(attr_name_no_suffix, None)
            if server is None:
                return None

        pkey = pkg_resources.resource_string(
            'yardstick.resources',
            h_join('files/yardstick_key', self.name)).decode('utf-8')

        result = {
            "user": server.context.user,
            "pkey": pkey,
            "private_ip": server.private_ip,
            "interfaces": server.interfaces,
            "routing_table": self.generate_routing_table(server),
            # empty IPv6 routing table
            "nd_route_tbl": [],
            # we want to save the contex name so we can generate pod.yaml
            "name": server.name,
        }
        # Target server may only have private_ip
        if server.public_ip:
            result["ip"] = server.public_ip

        return result

    def _get_network(self, attr_name):
        if not isinstance(attr_name, collections.Mapping):
            network = self.networks.get(attr_name, None)

        else:
            # Only take the first key, value
            key, value = next(iter(attr_name.items()), (None, None))
            if key is None:
                return None
            network_iter = (n for n in self.networks.values() if getattr(n, key) == value)
            network = next(network_iter, None)

        if network is None:
            return None

        result = {
            "name": network.name,
            "segmentation_id": network.segmentation_id,
            "network_type": network.network_type,
            "physical_network": network.physical_network,
        }
        return result
