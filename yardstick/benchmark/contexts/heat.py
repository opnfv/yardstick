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
from collections import OrderedDict

import ipaddress
import paramiko
import pkg_resources

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.model import Network
from yardstick.benchmark.contexts.model import PlacementGroup, ServerGroup
from yardstick.benchmark.contexts.model import Server
from yardstick.benchmark.contexts.model import update_scheduler_hints
from yardstick.common.openstack_utils import get_neutron_client
from yardstick.orchestrator.heat import HeatTemplate, get_short_key_uuid
from yardstick.common.constants import YARDSTICK_ROOT_PATH

LOG = logging.getLogger(__name__)

DEFAULT_HEAT_TIMEOUT = 3600


class HeatContext(Context):
    """Class that represents a context in the logical model"""

    __context_type__ = "Heat"

    def __init__(self):
        self.name = None
        self.stack = None
        self.networks = OrderedDict()
        self.servers = []
        self.placement_groups = []
        self.server_groups = []
        self.keypair_name = None
        self.secgroup_name = None
        self._server_map = {}
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
        self.key_filename = ''.join(
            [YARDSTICK_ROOT_PATH, 'yardstick/resources/files/yardstick_key-',
             get_short_key_uuid(self.key_uuid)])
        super(HeatContext, self).__init__()

    def assign_external_network(self, networks):
        sorted_networks = sorted(networks.items())
        external_network = os.environ.get("EXTERNAL_NETWORK", "net04_ext")
        have_external_network = [(name, net)
                                 for name, net in sorted_networks if
                                 net.get("external_network")]
        # no external net defined, assign it to first network usig os.environ
        if sorted_networks and not have_external_network:
            sorted_networks[0][1]["external_network"] = external_network
        return sorted_networks

    def init(self, attrs):     # pragma: no cover
        """initializes itself from the supplied arguments"""
        self.name = attrs["name"]

        self._user = attrs.get("user")

        self.template_file = attrs.get("heat_template")
        if self.template_file:
            self.heat_parameters = attrs.get("heat_parameters")
            return

        self.keypair_name = self.name + "-key"
        self.secgroup_name = self.name + "-secgroup"

        self._image = attrs.get("image")

        self._flavor = attrs.get("flavor")

        self.heat_timeout = attrs.get("timeout", DEFAULT_HEAT_TIMEOUT)

        self.placement_groups = [PlacementGroup(name, self, pgattrs["policy"])
                                 for name, pgattrs in attrs.get(
                                 "placement_groups", {}).items()]

        self.server_groups = [ServerGroup(name, self, sgattrs["policy"])
                              for name, sgattrs in attrs.get(
                              "server_groups", {}).items()]

        # we have to do this first, because we are injecting external_network
        # into the dict
        sorted_networks = self.assign_external_network(attrs["networks"])

        self.networks = OrderedDict(
            (name, Network(name, self, netattrs)) for name, netattrs in
            sorted_networks)

        for name, serverattrs in sorted(attrs["servers"].items()):
            server = Server(name, self, serverattrs)
            self.servers.append(server)
            self._server_map[server.dn] = server

        rsa_key = paramiko.RSAKey.generate(bits=2048, progress_func=None)
        rsa_key.write_private_key_file(self.key_filename)
        print("Writing %s ..." % self.key_filename)
        with open(self.key_filename + ".pub", "w") as pubkey_file:
            pubkey_file.write(
                "%s %s\n" % (rsa_key.get_name(), rsa_key.get_base64()))
        del rsa_key

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
                                 network.provider)
            template.add_subnet(network.subnet_stack_name, network.stack_name,
                                network.subnet_cidr)

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
                    self.flavors.add(server.stack_name + "-flavor")

        # add servers with availability policy
        added_servers = []
        for server in availability_servers:
            scheduler_hints = {}
            for pg in server.placement_groups:
                update_scheduler_hints(scheduler_hints, added_servers, pg)
            # workround for openstack nova bug, check JIRA: YARDSTICK-200
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
            raise
        # let the other failures happend, we want stack trace

        # TODO: use Neutron to get segementation-id
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
                network_name, port['stack_name'],
                server,
                self.stack.outputs)

    def make_interface_dict(self, network_name, stack_name, server, outputs):
        return {
            "private_ip": outputs[stack_name],
            "subnet_id": outputs[stack_name + "-subnet_id"],
            "subnet_cidr": outputs[
                "{}-{}-subnet-cidr".format(self.name, network_name)],
            "network": str(ipaddress.ip_network(
                outputs["{}-{}-subnet-cidr".format(self.name,
                                                   network_name)]).network_address),
            "netmask": str(ipaddress.ip_network(
                outputs["{}-{}-subnet-cidr".format(self.name,
                                                   network_name)]).netmask),
            "gateway_ip": outputs[
                "{}-{}-subnet-gateway_ip".format(self.name, network_name)],
            "mac_address": outputs[stack_name + "-mac_address"],
            "device_id": outputs[stack_name + "-device_id"],
            "network_id": outputs[stack_name + "-network_id"],
            "network_name": network_name,
            # to match vnf_generic
            "local_mac": outputs[stack_name + "-mac_address"],
            "local_ip": outputs[stack_name],
            "vld_id": self.networks[network_name].vld_id,
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
                "gateway": intf["gateway_ip"],
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
            'files/yardstick_key-' + get_short_key_uuid(self.key_uuid))

        if isinstance(attr_name, collections.Mapping):
            cname = attr_name["name"].split(".")[1]
            if cname != self.name:
                return None

            public_ip = None
            private_ip = None
            if "public_ip_attr" in attr_name:
                public_ip = self.stack.outputs[attr_name["public_ip_attr"]]
            if "private_ip_attr" in attr_name:
                private_ip = self.stack.outputs[
                    attr_name["private_ip_attr"]]

            # Create a dummy server instance for holding the *_ip attributes
            server = Server(attr_name["name"].split(".")[0], self, {})
            server.public_ip = public_ip
            server.private_ip = private_ip
        else:
            if attr_name not in self._server_map:
                return None
            server = self._server_map[attr_name]

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
        if isinstance(attr_name, collections.Mapping):
            # Don't generalize too much  Just support vld_id
            vld_id = attr_name.get('vld_id')
            if vld_id is None:
                return None
            try:
                network = next(n for n in self.networks.values() if
                               getattr(n, "vld_id") == vld_id)
            except StopIteration:
                return None

        else:
            network = self.networks[attr_name]

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
