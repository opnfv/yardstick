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
from __future__ import absolute_import
from six.moves import range


class Object(object):
    """Base class for classes in the logical model
    Contains common attributes and methods
    """

    def __init__(self, name, context):
        # model identities and reference
        self.name = name
        self._context = context

        # stack identities
        self.stack_name = None
        self.stack_id = None

    @property
    def dn(self):
        """returns distinguished name for object"""
        return self.name + "." + self._context.name


class PlacementGroup(Object):
    """Class that represents a placement group in the logical model
    Concept comes from the OVF specification. Policy should be one of
    "availability" or "affinity (there are more but they are not supported)"
    """
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
        return PlacementGroup.map.get(name)


class ServerGroup(Object):     # pragma: no cover
    """Class that represents a server group in the logical model
    Policy should be one of "anti-affinity" or "affinity"
    """
    map = {}

    def __init__(self, name, context, policy):
        super(ServerGroup, self).__init__(name, context)
        if policy not in {"affinity", "anti-affinity"}:
            raise ValueError("server group '%s', policy '%s' is not valid" %
                             (name, policy))
        self.name = name
        self.members = set()
        self.stack_name = context.name + "-" + name
        self.policy = policy
        ServerGroup.map[name] = self

    def add_member(self, name):
        self.members.add(name)

    @staticmethod
    def get(name):
        return ServerGroup.map.get(name)


class Router(Object):
    """Class that represents a router in the logical model"""

    def __init__(self, name, network_name, context, external_gateway_info):
        super(Router, self).__init__(name, context)

        self.stack_name = context.name + "-" + network_name + "-" + self.name
        self.stack_if_name = self.stack_name + "-if0"
        self.external_gateway_info = external_gateway_info


class Network(Object):
    """Class that represents a network in the logical model"""
    list = []

    def __init__(self, name, context, attrs):
        super(Network, self).__init__(name, context)
        self.stack_name = context.name + "-" + self.name
        self.subnet_stack_name = self.stack_name + "-subnet"
        self.subnet_cidr = attrs.get('cidr', '10.0.1.0/24')
        self.enable_dhcp = attrs.get('enable_dhcp', 'true')
        self.router = None
        self.physical_network = attrs.get('physical_network', 'physnet1')
        self.provider = attrs.get('provider')
        self.segmentation_id = attrs.get('segmentation_id')
        self.network_type = attrs.get('network_type')
        self.port_security_enabled = attrs.get('port_security_enabled')
        self.vnic_type = attrs.get('vnic_type', 'normal')
        self.allowed_address_pairs = attrs.get('allowed_address_pairs', [])
        try:
            # we require 'null' or '' to disable setting gateway_ip
            self.gateway_ip = attrs['gateway_ip']
        except KeyError:
            # default to explicit None
            self.gateway_ip = None
        else:
            # null is None in YAML, so we have to convert back to string
            if self.gateway_ip is None:
                self.gateway_ip = "null"

        if "external_network" in attrs:
            self.router = Router("router", self.name,
                                 context, attrs["external_network"])

        Network.list.append(self)

    def has_route_to(self, network_name):
        """determines if this network has a route to the named network"""
        if self.router and self.router.external_gateway_info == network_name:
            return True
        return False

    @staticmethod
    def find_by_route_to(external_network):
        """finds a network that has a route to the specified network"""
        for network in Network.list:
            if network.has_route_to(external_network):
                return network

    @staticmethod
    def find_external_network():
        """return the name of an external network some network in this
        context has a route to
        """
        for network in Network.list:
            if network.router:
                return network.router.external_gateway_info
        return None


class Server(Object):     # pragma: no cover
    """Class that represents a server in the logical model"""
    list = []

    def __init__(self, name, context, attrs):
        super(Server, self).__init__(name, context)
        self.stack_name = self.name + "." + context.name
        self.keypair_name = context.keypair_name
        self.secgroup_name = context.secgroup_name
        self.user = context.user
        self.context = context
        self.public_ip = None
        self.private_ip = None
        self.user_data = ''
        self.interfaces = {}

        if attrs is None:
            attrs = {}

        self.placement_groups = []
        placement = attrs.get("placement", [])
        placement = placement if isinstance(placement, list) else [placement]
        for p in placement:
            pg = PlacementGroup.get(p)
            if not pg:
                raise ValueError("server '%s', placement '%s' is invalid" %
                                 (name, p))
            self.placement_groups.append(pg)
            pg.add_member(self.stack_name)

        self.volume = None
        if "volume" in attrs:
            self.volume = attrs.get("volume")

        self.volume_mountpoint = None
        if "volume_mountpoint" in attrs:
            self.volume_mountpoint = attrs.get("volume_mountpoint")

        # support servergroup attr
        self.server_group = None
        sg = attrs.get("server_group")
        if sg:
            server_group = ServerGroup.get(sg)
            if not server_group:
                raise ValueError("server '%s', server_group '%s' is invalid" %
                                 (name, sg))
            self.server_group = server_group
            server_group.add_member(self.stack_name)

        self.instances = 1
        if "instances" in attrs:
            self.instances = attrs["instances"]

        # dict with key network name, each item is a dict with port name and ip
        self.ports = {}

        self.floating_ip = None
        self.floating_ip_assoc = None
        if "floating_ip" in attrs:
            self.floating_ip = {}
            self.floating_ip_assoc = {}

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

        self.user_data = attrs.get('user_data', '')

        Server.list.append(self)

    @property
    def image(self):
        """returns a server's image name"""
        if self._image:
            return self._image
        else:
            return self._context.image

    @property
    def flavor(self):
        """returns a server's flavor name"""
        if self._flavor:
            return self._flavor
        else:
            return self._context.flavor

    def _add_instance(self, template, server_name, networks, scheduler_hints):
        """adds to the template one server and corresponding resources"""
        port_name_list = []
        for network in networks:
            port_name = server_name + "-" + network.name + "-port"
            self.ports[network.name] = {"stack_name": port_name}
            # we can't use secgroups if port_security_enabled is False
            if network.port_security_enabled is False:
                sec_group_id = None
            else:
                # if port_security_enabled is None we still need to add to secgroup
                sec_group_id = self.secgroup_name
            # don't refactor to pass in network object, that causes JSON
            # circular ref encode errors
            template.add_port(port_name, network.stack_name, network.subnet_stack_name,
                              network.vnic_type, sec_group_id=sec_group_id,
                              provider=network.provider,
                              allowed_address_pairs=network.allowed_address_pairs)
            port_name_list.append(port_name)

            if self.floating_ip:
                external_network = self.floating_ip["external_network"]
                if network.has_route_to(external_network):
                    self.floating_ip["stack_name"] = server_name + "-fip"
                    template.add_floating_ip(self.floating_ip["stack_name"],
                                             external_network,
                                             port_name,
                                             network.router.stack_if_name,
                                             sec_group_id)
                    self.floating_ip_assoc["stack_name"] = \
                        server_name + "-fip-assoc"
                    template.add_floating_ip_association(
                        self.floating_ip_assoc["stack_name"],
                        self.floating_ip["stack_name"],
                        port_name)
        if self.flavor:
            if isinstance(self.flavor, dict):
                self.flavor["name"] = \
                    self.flavor.setdefault("name", self.stack_name + "-flavor")
                template.add_flavor(**self.flavor)
                self.flavor_name = self.flavor["name"]
            else:
                self.flavor_name = self.flavor

        if self.volume:
            if isinstance(self.volume, dict):
                self.volume["name"] = \
                    self.volume.setdefault("name", server_name + "-volume")
                template.add_volume(**self.volume)
                template.add_volume_attachment(server_name, self.volume["name"],
                                               mountpoint=self.volume_mountpoint)
            else:
                template.add_volume_attachment(server_name, self.volume,
                                               mountpoint=self.volume_mountpoint)

        template.add_server(server_name, self.image, flavor=self.flavor_name,
                            flavors=self.context.flavors,
                            ports=port_name_list,
                            user=self.user,
                            key_name=self.keypair_name,
                            user_data=self.user_data,
                            scheduler_hints=scheduler_hints)

    def add_to_template(self, template, networks, scheduler_hints=None):
        """adds to the template one or more servers (instances)"""
        if self.instances == 1:
            server_name = self.stack_name
            self._add_instance(template, server_name, networks,
                               scheduler_hints=scheduler_hints)
        else:
            # TODO(hafe) fix or remove, no test/sample for this
            for i in range(self.instances):
                server_name = "%s-%d" % (self.stack_name, i)
                self._add_instance(template, server_name, networks,
                                   scheduler_hints=scheduler_hints)


def update_scheduler_hints(scheduler_hints, added_servers, placement_group):
    """update scheduler hints from server's placement configuration
    TODO: this code is openstack specific and should move somewhere else
    """
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
