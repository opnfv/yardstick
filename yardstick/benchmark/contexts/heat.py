##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import sys

from yardstick.benchmark.contexts.base import Context
from yardstick.benchmark.contexts.model import Server
from yardstick.benchmark.contexts.model import PlacementGroup
from yardstick.benchmark.contexts.model import Network
from yardstick.benchmark.contexts.model import update_scheduler_hints
from yardstick.orchestrator.heat import HeatTemplate


class HeatContext(Context):
    '''Class that represents a context in the logical model'''

    __context_type__ = "Heat"

    def __init__(self):
        self.name = None
        self.stack = None
        self.networks = []
        self.servers = []
        self.placement_groups = []
        self.keypair_name = None
        self.secgroup_name = None
        self._server_map = {}
        self._image = None
        self._flavor = None
        self._user = None
        self.template_file = None
        self.heat_parameters = None
        super(self.__class__, self).__init__()

    def init(self, attrs):
        '''initializes itself from the supplied arguments'''
        self.name = attrs["name"]

        if "user" in attrs:
            self._user = attrs["user"]

        if "heat_template" in attrs:
            self.template_file = attrs["heat_template"]
            self.heat_parameters = attrs.get("heat_parameters", None)
            return

        self.keypair_name = self.name + "-key"
        self.secgroup_name = self.name + "-secgroup"

        if "image" in attrs:
            self._image = attrs["image"]

        if "flavor" in attrs:
            self._flavor = attrs["flavor"]

        if "placement_groups" in attrs:
            for name, pgattrs in attrs["placement_groups"].items():
                pg = PlacementGroup(name, self, pgattrs["policy"])
                self.placement_groups.append(pg)

        for name, netattrs in attrs["networks"].items():
            network = Network(name, self, netattrs)
            self.networks.append(network)

        for name, serverattrs in attrs["servers"].items():
            server = Server(name, self, serverattrs)
            self.servers.append(server)
            self._server_map[server.dn] = server

    @property
    def image(self):
        '''returns application's default image name'''
        return self._image

    @property
    def flavor(self):
        '''returns application's default flavor name'''
        return self._flavor

    @property
    def user(self):
        '''return login user name corresponding to image'''
        return self._user

    def _add_resources_to_template(self, template):
        '''add to the template the resources represented by this context'''
        template.add_keypair(self.keypair_name)
        template.add_security_group(self.secgroup_name)

        for network in self.networks:
            template.add_network(network.stack_name)
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

        # add servers with availability policy
        added_servers = []
        for server in availability_servers:
            scheduler_hints = {}
            for pg in server.placement_groups:
                update_scheduler_hints(scheduler_hints, added_servers, pg)
            server.add_to_template(template, self.networks, scheduler_hints)
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
            server.add_to_template(template, self.networks, scheduler_hints)
            added_servers.append(server.stack_name)

        # add remaining servers with no placement group configured
        for server in list_of_servers:
            if len(server.placement_groups) == 0:
                server.add_to_template(template, self.networks, {})

    def deploy(self):
        '''deploys template into a stack using cloud'''
        print "Deploying context '%s'" % self.name

        heat_template = HeatTemplate(self.name, self.template_file,
                                     self.heat_parameters)

        if self.template_file is None:
            self._add_resources_to_template(heat_template)

        try:
            self.stack = heat_template.create()
        except KeyboardInterrupt:
            sys.exit("\nStack create interrupted")
        except RuntimeError as err:
            sys.exit("error: failed to deploy stack: '%s'" % err.args)
        except Exception as err:
            sys.exit("error: failed to deploy stack: '%s'" % err)

        # copy some vital stack output into server objects
        for server in self.servers:
            if len(server.ports) > 0:
                # TODO(hafe) can only handle one internal network for now
                port = server.ports.values()[0]
                server.private_ip = self.stack.outputs[port["stack_name"]]

            if server.floating_ip:
                server.public_ip = \
                    self.stack.outputs[server.floating_ip["stack_name"]]

        print "Context '%s' deployed" % self.name

    def undeploy(self):
        '''undeploys stack from cloud'''
        if self.stack:
            print "Undeploying context '%s'" % self.name
            self.stack.delete()
            self.stack = None
            print "Context '%s' undeployed" % self.name

    def _get_server(self, attr_name):
        '''lookup server object by name from context
        attr_name: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        '''
        if type(attr_name) is dict:
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
            return server
        else:
            if attr_name not in self._server_map:
                return None
            return self._server_map[attr_name]
