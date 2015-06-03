##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Logical model

"""

import sys

from yardstick.orchestrator.heat import HeatTemplate


class Object(object):
    '''Base class for classes in the logical model
    Contains common attributes and methods
    '''
    def __init__(self, name, context):
        # model identities and reference
        self.name = name
        self._context = context

        # stack identities
        self.stack_name = None
        self.stack_id = None

    @property
    def dn(self):
        '''returns distinguished name for object'''
        return self.name + "." + self._context.name


class PlacementGroup(Object):
    '''Class that represents a placement group in the logical model
    Concept comes from the OVF specification. Policy should be one of
    "availability" or "affinity (there are more but they are not supported)"
    '''
    map = {}

    def __init__(self, name, context, policy):
        if policy not in ["affinity", "availability"]:
            raise ValueError("placement group '%s', policy '%s' is not valid" %
                             (name, policy))
        self.name = name
        self.members = set()
        self.stack_name = context.name + "-" + name
        self.policy = policy
        PlacementGroup.map[name] = self

    def add_member(self, name):
        self.members.add(name)

    @staticmethod
    def get(name):
        if name in PlacementGroup.map:
            return PlacementGroup.map[name]
        else:
            return None


class Router(Object):
    '''Class that represents a router in the logical model'''
    def __init__(self, name, network_name, context, external_gateway_info):
        super(Router, self).__init__(name, context)

        self.stack_name = context.name + "-" + network_name + "-" + self.name
        self.stack_if_name = self.stack_name + "-if0"
        self.external_gateway_info = external_gateway_info


class Network(Object):
    '''Class that represents a network in the logical model'''
    list = []

    def __init__(self, name, context, attrs):
        super(Network, self).__init__(name, context)
        self.stack_name = context.name + "-" + self.name
        self.subnet_stack_name = self.stack_name + "-subnet"
        self.subnet_cidr = attrs.get('cidr', '10.0.1.0/24')
        self.router = None

        if "external_network" in attrs:
            self.router = Router("router", self.name,
                                 context, attrs["external_network"])

        Network.list.append(self)

    def has_route_to(self, network_name):
        '''determines if this network has a route to the named network'''
        if self.router and self.router.external_gateway_info == network_name:
            return True
        return False

    @staticmethod
    def find_by_route_to(external_network):
        '''finds a network that has a route to the specified network'''
        for network in Network.list:
            if network.has_route_to(external_network):
                return network

    @staticmethod
    def find_external_network():
        '''return the name of an external network some network in this
        context has a route to'''
        for network in Network.list:
            if network.router:
                return network.router.external_gateway_info
        return None


class Server(Object):
    '''Class that represents a server in the logical model'''
    list = []

    def __init__(self, name, context, attrs):
        super(Server, self).__init__(name, context)
        self.stack_name = context.name + "-" + self.name
        self.keypair_name = context.keypair_name
        self.secgroup_name = context.secgroup_name
        self.context = context
        self.public_ip = None
        self.private_ip = None

        if attrs is None:
            attrs = {}

        self.placement_groups = []
        placement = attrs.get("placement", [])
        placement = placement if type(placement) is list else [placement]
        for p in placement:
            pg = PlacementGroup.get(p)
            if not pg:
                raise ValueError("server '%s', placement '%s' is invalid" %
                                 (name, p))
            self.placement_groups.append(pg)
            pg.add_member(self.stack_name)

        self.instances = 1
        if "instances" in attrs:
            self.instances = attrs["instances"]

        # dict with key network name, each item is a dict with port name and ip
        self.ports = {}

        self.floating_ip = None
        if "floating_ip" in attrs:
            self.floating_ip = {}

        if self.floating_ip is not None:
            ext_net = Network.find_external_network()
            assert ext_net is not None
            self.floating_ip["external_network"] = ext_net

        self._image = None
        if "image" in attrs:
            self._image = attrs["image"]

        self._flavor = None
        if "flavor" in attrs:
            self._flavor = attrs["flavor"]

        Server.list.append(self)

    @property
    def image(self):
        '''returns a server's image name'''
        if self._image:
            return self._image
        else:
            return self._context.image

    @property
    def flavor(self):
        '''returns a server's flavor name'''
        if self._flavor:
            return self._flavor
        else:
            return self._context.flavor

    def _add_instance(self, template, server_name, networks, scheduler_hints):
        '''adds to the template one server and corresponding resources'''
        port_name_list = []
        for network in networks:
            port_name = server_name + "-" + network.name + "-port"
            self.ports[network.name] = {"stack_name": port_name}
            template.add_port(port_name, network.stack_name,
                              network.subnet_stack_name,
                              sec_group_id=self.secgroup_name)
            port_name_list.append(port_name)

            if self.floating_ip:
                external_network = self.floating_ip["external_network"]
                if network.has_route_to(external_network):
                    self.floating_ip["stack_name"] = server_name + "-fip"
                    template.add_floating_ip(self.floating_ip["stack_name"],
                                             external_network,
                                             port_name,
                                             network.router.stack_if_name,
                                             self.secgroup_name)

        template.add_server(server_name, self.image, self.flavor,
                            ports=port_name_list,
                            key_name=self.keypair_name,
                            scheduler_hints=scheduler_hints)

    def add_to_template(self, template, networks, scheduler_hints=None):
        '''adds to the template one or more servers (instances)'''
        if self.instances == 1:
            server_name = "%s-%s" % (template.name, self.name)
            self._add_instance(template, server_name, networks,
                               scheduler_hints=scheduler_hints)
        else:
            for i in range(self.instances):
                server_name = "%s-%s-%d" % (template.name, self.name, i)
                self._add_instance(template, server_name, networks,
                                   scheduler_hints=scheduler_hints)


def update_scheduler_hints(scheduler_hints, added_servers, placement_group):
    ''' update scheduler hints from server's placement configuration
    TODO: this code is openstack specific and should move somewhere else
    '''
    if placement_group.policy == "affinity":
        if "same_host" in scheduler_hints:
            host_list = scheduler_hints["same_host"]
        else:
            host_list = scheduler_hints["same_host"] = []
    else:
        if "different_host" in scheduler_hints:
            host_list = scheduler_hints["different_host"]
        else:
            host_list = scheduler_hints["different_host"] = []

    for name in added_servers:
        if name in placement_group.members:
            host_list.append({'get_resource': name})


class Context(object):
    '''Class that represents a context in the logical model'''
    list = []

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
        Context.list.append(self)

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

        availability_servers = []
        for server in list_of_servers:
            for pg in server.placement_groups:
                if pg.policy == "availability":
                    availability_servers.append(server)
                    break

        # add servers with scheduler hints derived from placement groups
        added_servers = []
        for server in availability_servers:
            scheduler_hints = {}
            for pg in server.placement_groups:
                update_scheduler_hints(scheduler_hints, added_servers, pg)
            server.add_to_template(template, self.networks, scheduler_hints)
            added_servers.append(server.stack_name)

        affinity_servers = []
        for server in list_of_servers:
            for pg in server.placement_groups:
                if pg.policy == "affinity":
                    affinity_servers.append(server)
                    break

        for server in affinity_servers:
            if server.stack_name in added_servers:
                continue
            scheduler_hints = {}
            for pg in server.placement_groups:
                update_scheduler_hints(scheduler_hints, added_servers, pg)
            server.add_to_template(template, self.networks, scheduler_hints)
            added_servers.append(server.stack_name)

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

    @staticmethod
    def get_server_by_name(dn):
        '''lookup server object by DN

        dn is a distinguished name including the context name'''
        if "." not in dn:
            raise ValueError("dn '%s' is malformed" % dn)

        for context in Context.list:
            if dn in context._server_map:
                return context._server_map[dn]

        return None

    @staticmethod
    def get_context_by_name(name):
        for context in Context.list:
            if name == context.name:
                return context
        return None

    @staticmethod
    def get_server(attr_name):
        '''lookup server object by name from context
        attr_name: either a name for a server created by yardstick or a dict
        with attribute name mapping when using external heat templates
        '''
        if type(attr_name) is dict:
            cname = attr_name["name"].split(".")[1]
            context = Context.get_context_by_name(cname)
            if context is None:
                raise ValueError("context not found for server '%s'" %
                                 attr_name["name"])

            public_ip = None
            private_ip = None
            if "public_ip_attr" in attr_name:
                public_ip = context.stack.outputs[attr_name["public_ip_attr"]]
            if "private_ip_attr" in attr_name:
                private_ip = context.stack.outputs[
                    attr_name["private_ip_attr"]]

            # Create a dummy server instance for holding the *_ip attributes
            server = Server(attr_name["name"].split(".")[0], context, {})
            server.public_ip = public_ip
            server.private_ip = private_ip
            return server
        else:
            return Context.get_server_by_name(attr_name)
