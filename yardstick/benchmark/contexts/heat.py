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
import uuid
import errno
from collections import OrderedDict

import ipaddress
import pkg_resources

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.model import Network
from yardstick.benchmark.contexts.model import PlacementGroup, ServerGroup
from yardstick.benchmark.contexts.model import Server
from yardstick.benchmark.contexts.model import update_scheduler_hints
from yardstick.common.openstack_utils import get_neutron_client
from yardstick.orchestrator.heat import HeatTemplate, get_short_key_uuid
from yardstick.common import constants as consts
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
        self.name = None
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
        self.neutron_client = None
        # generate an uuid to identify yardstick_key
        # the first 8 digits of the uuid will be used
        self.key_uuid = uuid.uuid4()
        self.heat_timeout = None
        self.key_filename = ''.join(
            [consts.YARDSTICK_ROOT_PATH, 'yardstick/resources/files/yardstick_key-',
             get_short_key_uuid(self.key_uuid)])
        super(HeatContext, self).__init__()

    @staticmethod
    def assign_external_network(networks):
        sorted_networks = sorted(networks.items())
        external_network = os.environ.get("EXTERNAL_NETWORK", "net04_ext")

        have_external_network = any(net.get("external_network") for net in networks.values())
        if sorted_networks and not have_external_network:
            # no external net defined, assign it to first network using os.environ
            sorted_networks[0][1]["external_network"] = external_network

        return sorted_networks

    def init(self, attrs):
        self.check_environment()
        """initializes itself from the supplied arguments"""
        self.name = attrs["name"]

        self._user = attrs.get("user")

        self.template_file = attrs.get("heat_template")
        if self.template_file:
            self.heat_parameters = attrs.get("heat_parameters")
            return

        self.keypair_name = h_join(self.name, "key")
        self.secgroup_name = h_join(self.name, "secgroup")

        self._image = attrs.get("image")

        self._flavor = attrs.get("flavor")

        self.heat_timeout = attrs.get("timeout", DEFAULT_HEAT_TIMEOUT)

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
        SSH.gen_keys(self.key_filename)

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

        template.add_keypair(self.keypair_name, self.key_uuid)
        template.add_security_group(self.secgroup_name)

        for network in self.networks.values():
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
        if not self.neutron_client:
            self.neutron_client = get_neutron_client()

        networks = self.neutron_client.list_networks()
        for network in self.networks.values():
            for neutron_net in networks['networks']:
                if neutron_net['name'] == network.stack_name:
                    network.segmentation_id = neutron_net.get('provider:segmentation_id')
                    # we already have physical_network
                    # network.physical_network = neutron_net.get('provider:physical_network')
                    network.network_type = neutron_net.get('provider:network_type')
                    network.neutron_info = neutron_net

    def deploy(self):
        """deploys template into a stack using cloud"""
        print("Deploying context '%s'" % self.name)

        heat_template = HeatTemplate(self.name, self.template_file,
                                     self.heat_parameters)

        if self.template_file is None:
            self._add_resources_to_template(heat_template)

        try:
            self.stack = heat_template.create(block=True,
                                              timeout=self.heat_timeout)
        except KeyboardInterrupt:
            raise SystemExit("\nStack create interrupted")
        except:
            LOG.exception("stack failed")
            # let the other failures happen, we want stack trace
            raise

        # TODO: use Neutron to get segmentation-id
        self.get_neutron_info()

        # copy some vital stack output into server objects
        for server in self.servers:
            if server.ports:
                self.add_server_port(server)

            if server.floating_ip:
                server.public_ip = \
                    self.stack.outputs[server.floating_ip["stack_name"]]

        print("Context '%s' deployed" % self.name)

    def add_server_port(self, server):
        # TODO(hafe) can only handle one internal network for now
        port = next(iter(server.ports.values()))
        server.private_ip = self.stack.outputs[port["stack_name"]]
        server.interfaces = {}
        for network_name, port in server.ports.items():
            server.interfaces[network_name] = self.make_interface_dict(
                network_name, port['stack_name'], self.stack.outputs)

    def make_interface_dict(self, network_name, stack_name, outputs):
        private_ip = outputs[stack_name]
        mac_address = outputs[h_join(stack_name, "mac_address")]
        output_subnet_cidr = outputs[h_join(self.name, network_name,
                                            'subnet', 'cidr')]

        output_subnet_gateway = outputs[h_join(self.name, network_name,
                                               'subnet', 'gateway_ip')]

        return {
            "private_ip": private_ip,
            "subnet_id": outputs[h_join(stack_name, "subnet_id")],
            "subnet_cidr": output_subnet_cidr,
            "network": str(ipaddress.ip_network(output_subnet_cidr).network_address),
            "netmask": str(ipaddress.ip_network(output_subnet_cidr).netmask),
            "gateway_ip": output_subnet_gateway,
            "mac_address": mac_address,
            "device_id": outputs[h_join(stack_name, "device_id")],
            "network_id": outputs[h_join(stack_name, "network_id")],
            "network_name": network_name,
            # to match vnf_generic
            "local_mac": mac_address,
            "local_ip": private_ip,
        }

    def undeploy(self):
        """undeploys stack from cloud"""
        if self.stack:
            print("Undeploying context '%s'" % self.name)
            self.stack.delete()
            self.stack = None
            print("Context '%s' undeployed" % self.name)

        if os.path.exists(self.key_filename):
            try:
                os.remove(self.key_filename)
                os.remove(self.key_filename + ".pub")
            except OSError:
                LOG.exception("Key filename %s", self.key_filename)

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
        key_filename = pkg_resources.resource_filename(
            'yardstick.resources',
            h_join('files/yardstick_key', get_short_key_uuid(self.key_uuid)))

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
            server = self._server_map.get(attr_name, None)
            if server is None:
                return None

        result = {
            "user": server.context.user,
            "key_filename": key_filename,
            "private_ip": server.private_ip,
            "interfaces": server.interfaces,
            "routing_table": self.generate_routing_table(server),
            # empty IPv6 routing table
            "nd_route_tbl": [],
        }
        # Target server may only have private_ip
        if server.public_ip:
            result["ip"] = server.public_ip

        return result

    def _get_network(self, attr_name):
        if not isinstance(attr_name, collections.Mapping):
            network = self.networks.get(attr_name, None)

        else:
            # Don't generalize too much  Just support vld_id
            vld_id = attr_name.get('vld_id', {})
            network_iter = (n for n in self.networks.values() if n.vld_id == vld_id)
            network = next(network_iter, None)

        if network is None:
            return None

        result = {
            "name": network.name,
            "vld_id": network.vld_id,
            "segmentation_id": network.segmentation_id,
            "network_type": network.network_type,
            "physical_network": network.physical_network,
        }
        return result
