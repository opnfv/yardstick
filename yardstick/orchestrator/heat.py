#############################################################################
# Copyright (c) 2015-2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""Heat template and stack management"""

from __future__ import absolute_import
import collections
import datetime
import getpass
import logging
import pkg_resources
import pprint
import socket
import tempfile
import time

from oslo_serialization import jsonutils
from oslo_utils import encodeutils
import shade
from shade._heat import event_utils

import yardstick.common.openstack_utils as op_utils
from yardstick.common import exceptions
from yardstick.common import template_format
from yardstick.common import constants as consts

log = logging.getLogger(__name__)


PROVIDER_SRIOV = "sriov"

_DEPLOYED_STACKS = {}


class HeatStack(object):
    """Represents a Heat stack (deployed template) """

    def __init__(self, name):
        self.name = name
        self.outputs = {}
        self._cloud = shade.openstack_cloud()
        self._stack = None

    def _update_stack_tracking(self):
        outputs = self._stack.outputs
        self.outputs = {output['output_key']: output['output_value'] for output
                        in outputs}
        if self.uuid:
            _DEPLOYED_STACKS[self.uuid] = self._stack

    def create(self, template, heat_parameters, wait, timeout):
        """Creates an OpenStack stack from a template"""
        with tempfile.NamedTemporaryFile('wb', delete=False) as template_file:
            template_file.write(jsonutils.dump_as_bytes(template))
            template_file.close()
            self._stack = self._cloud.create_stack(
                self.name, template_file=template_file.name, wait=wait,
                timeout=timeout, **heat_parameters)

        self._update_stack_tracking()

    def get_failures(self):
        return event_utils.get_events(self._cloud, self._stack.id,
                                      event_args={'resource_status': 'FAILED'})

    def get(self):
        """Retrieves an existing stack from the target cloud

        Returns a bool indicating whether the stack exists in the target cloud
        If the stack exists, it will be stored as self._stack
        """
        self._stack = self._cloud.get_stack(self.name)
        if not self._stack:
            return False

        self._update_stack_tracking()
        return True

    @staticmethod
    def stacks_exist():
        """Check if any stack has been deployed"""
        return len(_DEPLOYED_STACKS) > 0

    def delete(self, wait=True):
        """Deletes a stack in the target cloud"""
        if self.uuid is None:
            return

        try:
            ret = self._cloud.delete_stack(self.uuid, wait=wait)
        except TypeError:
            # NOTE(ralonsoh): this exception catch solves a bug in Shade, which
            # tries to retrieve and read the stack status when it's already
            # deleted.
            ret = True

        _DEPLOYED_STACKS.pop(self.uuid)
        self._stack = None
        return ret

    @staticmethod
    def delete_all():
        """Delete all deployed stacks"""
        for stack in _DEPLOYED_STACKS:
            stack.delete()

    @property
    def status(self):
        """Retrieve the current stack status"""
        if self._stack:
            return self._stack.status

    @property
    def uuid(self):
        """Retrieve the current stack ID"""
        if self._stack:
            return self._stack.id


class HeatTemplate(object):
    """Describes a Heat template and a method to deploy template to a stack"""

    DESCRIPTION_TEMPLATE = """
Stack built by the yardstick framework for %s on host %s %s.
All referred generated resources are prefixed with the template
name (i.e. %s).
"""

    HEAT_WAIT_LOOP_INTERVAL = 2
    HEAT_STATUS_COMPLETE = 'COMPLETE'

    def _init_template(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._template = {
            'heat_template_version': '2013-05-23',
            'description': self.DESCRIPTION_TEMPLATE % (
                getpass.getuser(),
                socket.gethostname(),
                timestamp,
                self.name
            ),
            'resources': {},
            'outputs': {}
        }

        # short hand for resources part of template
        self.resources = self._template['resources']

    def __init__(self, name, template_file=None, heat_parameters=None):
        self.name = name
        self.keystone_client = None
        self.heat_parameters = {}

        # heat_parameters is passed to heat in stack create, empty dict when
        # yardstick creates the template (no get_param in resources part)
        if heat_parameters:
            self.heat_parameters = heat_parameters

        if template_file:
            with open(template_file) as stream:
                log.info('Parsing external template: %s', template_file)
                template_str = stream.read()
            self._template = template_format.parse(template_str)
            self._parameters = heat_parameters
        else:
            self._init_template()

        log.debug("template object '%s' created", name)

    def add_flavor(self, name, vcpus=1, ram=1024, disk=1, ephemeral=0,
                   is_public=True, rxtx_factor=1.0, swap=0,
                   extra_specs=None):
        """add to the template a Flavor description"""
        if name is None:
            name = 'auto'
        log.debug("adding Nova::Flavor '%s' vcpus '%d' ram '%d' disk '%d' "
                  "ephemeral '%d' is_public '%s' rxtx_factor '%d' "
                  "swap '%d' extra_specs '%s'",
                  name, vcpus, ram, disk, ephemeral, is_public,
                  rxtx_factor, swap, str(extra_specs))

        if extra_specs:
            assert isinstance(extra_specs, collections.Mapping)

        self.resources[name] = {
            'type': 'OS::Nova::Flavor',
            'properties': {'name': name,
                           'disk': disk,
                           'vcpus': vcpus,
                           'swap': swap,
                           'flavorid': name,
                           'rxtx_factor': rxtx_factor,
                           'ram': ram,
                           'is_public': is_public,
                           'ephemeral': ephemeral,
                           'extra_specs': extra_specs}
        }

        self._template['outputs'][name] = {
            'description': 'Flavor %s ID' % name,
            'value': {'get_resource': name}
        }

    def add_volume(self, name, size=10):
        """add to the template a volume description"""
        log.debug("adding Cinder::Volume '%s' size '%d' ", name, size)

        self.resources[name] = {
            'type': 'OS::Cinder::Volume',
            'properties': {'name': name,
                           'size': size}
        }

        self._template['outputs'][name] = {
            'description': 'Volume %s ID' % name,
            'value': {'get_resource': name}
        }

    def add_volume_attachment(self, server_name, volume_name, mountpoint=None):
        """add to the template an association of volume to instance"""
        log.debug("adding Cinder::VolumeAttachment server '%s' volume '%s' ", server_name,
                  volume_name)

        name = "%s-%s" % (server_name, volume_name)

        volume_id = op_utils.get_volume_id(volume_name)
        if not volume_id:
            volume_id = {'get_resource': volume_name}
        self.resources[name] = {
            'type': 'OS::Cinder::VolumeAttachment',
            'properties': {'instance_uuid': {'get_resource': server_name},
                           'volume_id': volume_id}
        }

        if mountpoint:
            self.resources[name]['properties']['mountpoint'] = mountpoint

    def add_network(self, name, physical_network='physnet1', provider=None,
                    segmentation_id=None, port_security_enabled=None, network_type=None):
        """add to the template a Neutron Net"""
        log.debug("adding Neutron::Net '%s'", name)
        if provider is None:
            self.resources[name] = {
                'type': 'OS::Neutron::Net',
                'properties': {
                    'name': name,
                }
            }
        else:
            self.resources[name] = {
                'type': 'OS::Neutron::ProviderNet',
                'properties': {
                    'name': name,
                    'network_type': 'flat' if network_type is None else network_type,
                    'physical_network': physical_network,
                },
            }
            if segmentation_id:
                self.resources[name]['properties']['segmentation_id'] = segmentation_id
                if network_type is None:
                    self.resources[name]['properties']['network_type'] = 'vlan'
        # if port security is not defined then don't add to template:
        # some deployments don't have port security plugin installed
        if port_security_enabled is not None:
            self.resources[name]['properties']['port_security_enabled'] = port_security_enabled

    def add_server_group(self, name, policies):     # pragma: no cover
        """add to the template a ServerGroup"""
        log.debug("adding Nova::ServerGroup '%s'", name)
        policies = policies if isinstance(policies, list) else [policies]
        self.resources[name] = {
            'type': 'OS::Nova::ServerGroup',
            'properties': {'name': name,
                           'policies': policies}
        }

    def add_subnet(self, name, network, cidr, enable_dhcp='true', gateway_ip=None):
        """add to the template a Neutron Subnet
        """
        log.debug("adding Neutron::Subnet '%s' in network '%s', cidr '%s'",
                  name, network, cidr)
        self.resources[name] = {
            'type': 'OS::Neutron::Subnet',
            'depends_on': network,
            'properties': {
                'name': name,
                'cidr': cidr,
                'network_id': {'get_resource': network},
                'enable_dhcp': enable_dhcp,
            }
        }
        if gateway_ip == 'null':
            self.resources[name]['properties']['gateway_ip'] = None
        elif gateway_ip is not None:
            self.resources[name]['properties']['gateway_ip'] = gateway_ip

        self._template['outputs'][name] = {
            'description': 'subnet %s ID' % name,
            'value': {'get_resource': name}
        }
        self._template['outputs'][name + "-cidr"] = {
            'description': 'subnet %s cidr' % name,
            'value': {'get_attr': [name, 'cidr']}
        }
        self._template['outputs'][name + "-gateway_ip"] = {
            'description': 'subnet %s gateway_ip' % name,
            'value': {'get_attr': [name, 'gateway_ip']}
        }

    def add_router(self, name, ext_gw_net, subnet_name):
        """add to the template a Neutron Router and interface"""
        log.debug("adding Neutron::Router:'%s', gw-net:'%s'", name, ext_gw_net)
        self.resources[name] = {
            'type': 'OS::Neutron::Router',
            'depends_on': [subnet_name],
            'properties': {
                'name': name,
                'external_gateway_info': {
                    'network': ext_gw_net
                }
            }
        }

    def add_router_interface(self, name, router_name, subnet_name):
        """add to the template a Neutron RouterInterface and interface"""
        log.debug("adding Neutron::RouterInterface '%s' router:'%s', "
                  "subnet:'%s'", name, router_name, subnet_name)
        self.resources[name] = {
            'type': 'OS::Neutron::RouterInterface',
            'depends_on': [router_name, subnet_name],
            'properties': {
                'router_id': {'get_resource': router_name},
                'subnet_id': {'get_resource': subnet_name}
            }
        }

    def add_port(self, name, network, sec_group_id=None,
                 provider=None, allowed_address_pairs=None):
        """add to the template a named Neutron Port
        """
        net_is_existing = network.net_flags.get(consts.IS_EXISTING)
        depends_on = [] if net_is_existing else [network.subnet_stack_name]
        fixed_ips = [{'subnet': network.subnet}] if net_is_existing else [
            {'subnet': {'get_resource': network.subnet_stack_name}}]
        network_ = network.name if net_is_existing else {
            'get_resource': network.stack_name}
        self.resources[name] = {
            'type': 'OS::Neutron::Port',
            'depends_on': depends_on,
            'properties': {
                'name': name,
                'binding:vnic_type': network.vnic_type,
                'fixed_ips': fixed_ips,
                'network': network_,
            }
        }

        if provider == PROVIDER_SRIOV:
            self.resources[name]['properties']['binding:vnic_type'] = \
                'direct'

        if sec_group_id:
            self.resources[name]['depends_on'].append(sec_group_id)
            self.resources[name]['properties']['security_groups'] = \
                [sec_group_id]

        if allowed_address_pairs:
            self.resources[name]['properties'][
                'allowed_address_pairs'] = allowed_address_pairs

        log.debug("adding Neutron::Port %s", self.resources[name])

        self._template['outputs'][name] = {
            'description': 'Address for interface %s' % name,
            'value': {'get_attr': [name, 'fixed_ips', 0, 'ip_address']}
        }
        self._template['outputs'][name + "-subnet_id"] = {
            'description': 'Address for interface %s' % name,
            'value': {'get_attr': [name, 'fixed_ips', 0, 'subnet_id']}
        }
        self._template['outputs'][name + "-mac_address"] = {
            'description': 'MAC Address for interface %s' % name,
            'value': {'get_attr': [name, 'mac_address']}
        }
        self._template['outputs'][name + "-device_id"] = {
            'description': 'Device ID for interface %s' % name,
            'value': {'get_attr': [name, 'device_id']}
        }
        self._template['outputs'][name + "-network_id"] = {
            'description': 'Network ID for interface %s' % name,
            'value': {'get_attr': [name, 'network_id']}
        }

    def add_floating_ip(self, name, network_name, port_name, router_if_name,
                        secgroup_name=None):
        """add to the template a Nova FloatingIP resource
        see: https://bugs.launchpad.net/heat/+bug/1299259
        """
        log.debug("adding Nova::FloatingIP '%s', network '%s', port '%s', "
                  "rif '%s'", name, network_name, port_name, router_if_name)

        self.resources[name] = {
            'type': 'OS::Nova::FloatingIP',
            'depends_on': [port_name, router_if_name],
            'properties': {
                'pool': network_name
            }
        }

        if secgroup_name:
            self.resources[name]["depends_on"].append(secgroup_name)

        self._template['outputs'][name] = {
            'description': 'floating ip %s' % name,
            'value': {'get_attr': [name, 'ip']}
        }

    def add_floating_ip_association(self, name, floating_ip_name, port_name):
        """add to the template a Nova FloatingIP Association resource
        """
        log.debug("adding Nova::FloatingIPAssociation '%s', server '%s', "
                  "floating_ip '%s'", name, port_name, floating_ip_name)

        self.resources[name] = {
            'type': 'OS::Neutron::FloatingIPAssociation',
            'depends_on': [port_name],
            'properties': {
                'floatingip_id': {'get_resource': floating_ip_name},
                'port_id': {'get_resource': port_name}
            }
        }

    def add_keypair(self, name, key_id):
        """add to the template a Nova KeyPair"""
        log.debug("adding Nova::KeyPair '%s'", name)
        self.resources[name] = {
            'type': 'OS::Nova::KeyPair',
            'properties': {
                'name': name,
                # resource_string returns bytes, so we must decode to unicode
                'public_key': encodeutils.safe_decode(
                    pkg_resources.resource_string(
                        'yardstick.resources',
                        'files/yardstick_key-' +
                        key_id + '.pub'),
                    'utf-8')
            }
        }

    def add_servergroup(self, name, policy):
        """add to the template a Nova ServerGroup"""
        log.debug("adding Nova::ServerGroup '%s', policy '%s'", name, policy)
        if policy not in ["anti-affinity", "affinity"]:
            raise ValueError(policy)

        self.resources[name] = {
            'type': 'OS::Nova::ServerGroup',
            'properties': {
                'name': name,
                'policies': [policy]
            }
        }

        self._template['outputs'][name] = {
            'description': 'ID Server Group %s' % name,
            'value': {'get_resource': name}
        }

    def add_security_group(self, name):
        """add to the template a Neutron SecurityGroup"""
        log.debug("adding Neutron::SecurityGroup '%s'", name)
        self.resources[name] = {
            'type': 'OS::Neutron::SecurityGroup',
            'properties': {
                'name': name,
                'description': "Group allowing IPv4 and IPv6 for icmp and upd/tcp on all ports",
                'rules': [
                    {'remote_ip_prefix': '0.0.0.0/0',
                     'protocol': 'tcp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '0.0.0.0/0',
                     'protocol': 'udp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '0.0.0.0/0',
                     'protocol': 'icmp'},
                    {'remote_ip_prefix': '::/0',
                     'ethertype': 'IPv6',
                     'protocol': 'tcp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '::/0',
                     'ethertype': 'IPv6',
                     'protocol': 'udp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '::/0',
                     'ethertype': 'IPv6',
                     'protocol': 'ipv6-icmp'},
                    {'remote_ip_prefix': '0.0.0.0/0',
                     'direction': 'egress',
                     'protocol': 'tcp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '0.0.0.0/0',
                     'direction': 'egress',
                     'protocol': 'udp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '0.0.0.0/0',
                     'direction': 'egress',
                     'protocol': 'icmp'},
                    {'remote_ip_prefix': '::/0',
                     'direction': 'egress',
                     'ethertype': 'IPv6',
                     'protocol': 'tcp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '::/0',
                     'direction': 'egress',
                     'ethertype': 'IPv6',
                     'protocol': 'udp',
                     'port_range_min': '1',
                     'port_range_max': '65535'},
                    {'remote_ip_prefix': '::/0',
                     'direction': 'egress',
                     'ethertype': 'IPv6',
                     'protocol': 'ipv6-icmp'},
                ]
            }
        }

        self._template['outputs'][name] = {
            'description': 'ID of Security Group',
            'value': {'get_resource': name}
        }

    def add_server(self, name, image, flavor, flavors, ports=None, networks=None,
                   scheduler_hints=None, user=None, key_name=None, user_data=None, metadata=None,
                   additional_properties=None, availability_zone=None):
        """add to the template a Nova Server """
        log.debug("adding Nova::Server '%s', image '%s', flavor '%s', "
                  "ports %s", name, image, flavor, ports)

        self.resources[name] = {
            'type': 'OS::Nova::Server',
            'depends_on': []
        }

        server_properties = {
            'name': name,
            'image': image,
            'flavor': {},
            'networks': []  # list of dictionaries
        }
        if availability_zone:
            server_properties["availability_zone"] = availability_zone

        if flavor in flavors:
            self.resources[name]['depends_on'].append(flavor)
            server_properties["flavor"] = {'get_resource': flavor}
        else:
            server_properties["flavor"] = flavor

        if user:
            server_properties['admin_user'] = user

        if key_name:
            self.resources[name]['depends_on'].append(key_name)
            server_properties['key_name'] = {'get_resource': key_name}

        if ports:
            self.resources[name]['depends_on'].extend(ports)
            for port in ports:
                server_properties['networks'].append(
                    {'port': {'get_resource': port}}
                )

        if networks:
            for i, _ in enumerate(networks):
                server_properties['networks'].append({'network': networks[i]})

        if scheduler_hints:
            server_properties['scheduler_hints'] = scheduler_hints

        if user_data:
            server_properties['user_data'] = user_data

        if metadata:
            assert isinstance(metadata, collections.Mapping)
            server_properties['metadata'] = metadata

        if additional_properties:
            assert isinstance(additional_properties, collections.Mapping)
            for prop in additional_properties:
                server_properties[prop] = additional_properties[prop]

        server_properties['config_drive'] = True

        self.resources[name]['properties'] = server_properties

        self._template['outputs'][name] = {
            'description': 'VM UUID',
            'value': {'get_resource': name}
        }

    def create(self, block=True, timeout=3600):
        """Creates a stack in the target based on the stored template

        :param block: (bool) Wait for Heat create to finish
        :param timeout: (int) Timeout in seconds for Heat create,
               default 3600s
        :return A dict with the requested output values from the template
        """
        log.info("Creating stack '%s' START", self.name)

        start_time = time.time()
        stack = HeatStack(self.name)
        stack.create(self._template, self.heat_parameters, block, timeout)

        if not block:
            log.info("Creating stack '%s' DONE in %d secs",
                     self.name, time.time() - start_time)
            return stack

        if stack.status != self.HEAT_STATUS_COMPLETE:
            for event in stack.get_failures():
                log.error("%s", event.resource_status_reason)
            log.error(pprint.pformat(self._template))
            raise exceptions.HeatTemplateError(stack_name=self.name)

        log.info("Creating stack '%s' DONE in %d secs",
                 self.name, time.time() - start_time)
        return stack
