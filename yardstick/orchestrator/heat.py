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
from __future__ import print_function
from six.moves import range

import collections
import datetime
import getpass
import logging

import socket
import time

import heatclient.client
import pkg_resources

from oslo_utils import encodeutils

import yardstick.common.openstack_utils as op_utils
from yardstick.common import template_format

log = logging.getLogger(__name__)


HEAT_KEY_UUID_LENGTH = 8

PROVIDER_SRIOV = "sriov"


def get_short_key_uuid(uuid):
    return str(uuid)[:HEAT_KEY_UUID_LENGTH]


class HeatObject(object):
    """base class for template and stack"""

    def __init__(self):
        self._heat_client = None
        self.uuid = None

    @property
    def heat_client(self):
        """returns a heat client instance"""

        if self._heat_client is None:
            sess = op_utils.get_session()
            heat_endpoint = op_utils.get_endpoint(service_type='orchestration')
            self._heat_client = heatclient.client.Client(
                op_utils.get_heat_api_version(),
                endpoint=heat_endpoint, session=sess)

        return self._heat_client

    def status(self):
        """returns stack state as a string"""
        heat_client = self.heat_client
        stack = heat_client.stacks.get(self.uuid)
        return stack.stack_status


class HeatStack(HeatObject):
    """Represents a Heat stack (deployed template) """
    stacks = []

    def __init__(self, name):
        super(HeatStack, self).__init__()
        self.uuid = None
        self.name = name
        self.outputs = None
        HeatStack.stacks.append(self)

    @staticmethod
    def stacks_exist():
        """check if any stack has been deployed"""
        return len(HeatStack.stacks) > 0

    def _delete(self):
        """deletes a stack from the target cloud using heat"""
        if self.uuid is None:
            return

        log.info("Deleting stack '%s', uuid:%s", self.name, self.uuid)
        heat = self.heat_client
        template = heat.stacks.get(self.uuid)
        start_time = time.time()
        template.delete()

        for status in iter(self.status, u'DELETE_COMPLETE'):
            log.debug("stack state %s", status)
            if status == u'DELETE_FAILED':
                raise RuntimeError(
                    heat.stacks.get(self.uuid).stack_status_reason)

            time.sleep(2)

        end_time = time.time()
        log.info("Deleted stack '%s' in %d secs", self.name,
                 end_time - start_time)
        self.uuid = None

    def delete(self, block=True, retries=3):
        """deletes a stack in the target cloud using heat (with retry)
        Sometimes delete fail with "InternalServerError" and the next attempt
        succeeds. So it is worthwhile to test a couple of times.
        """
        if self.uuid is None:
            return

        if not block:
            self._delete()
            return

        for _ in range(retries):
            try:
                self._delete()
                break
            except RuntimeError as err:
                log.warning(err.args)
                time.sleep(2)

        # if still not deleted try once more and let it fail everything
        if self.uuid is not None:
            self._delete()

        HeatStack.stacks.remove(self)

    @staticmethod
    def delete_all():
        for stack in HeatStack.stacks[:]:
            stack.delete()

    def update(self):
        """update a stack"""
        raise RuntimeError("not implemented")


class HeatTemplate(HeatObject):
    """Describes a Heat template and a method to deploy template to a stack"""

    DESCRIPTION_TEMPLATE = """\
Stack built by the yardstick framework for %s on host %s %s.
All referred generated resources are prefixed with the template
name (i.e. %s).\
"""

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
        super(HeatTemplate, self).__init__()
        self.name = name
        self.state = "NOT_CREATED"
        self.keystone_client = None
        self.heat_parameters = {}

        # heat_parameters is passed to heat in stack create, empty dict when
        # yardstick creates the template (no get_param in resources part)
        if heat_parameters:
            self.heat_parameters = heat_parameters

        if template_file:
            with open(template_file) as stream:
                print("Parsing external template:", template_file)
                template_str = stream.read()
            self._template = template_format.parse(template_str)
            self._parameters = heat_parameters
        else:
            self._init_template()

        # holds results of requested output after deployment
        self.outputs = {}

        log.debug("template object '%s' created", name)

    def add_flavor(self, name, vcpus=1, ram=1024, disk=1, ephemeral=0,
                   is_public=True, rxtx_factor=1.0, swap=0,
                   extra_specs=None):
        """add to the template a Flavor description"""
        if name is None:
            name = 'auto'
        log.debug("adding Nova::Flavor '%s' vcpus '%d' ram '%d' disk '%d' " +
                  "ephemeral '%d' is_public '%s' rxtx_factor '%d' " +
                  "swap '%d' extra_specs '%s' ",
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

    def add_port(self, name, network_name, subnet_name, vnic_type, sec_group_id=None,
                 provider=None, allowed_address_pairs=None):
        """add to the template a named Neutron Port
        """
        log.debug("adding Neutron::Port '%s', network:'%s', subnet:'%s', vnic_type:'%s', "
                  "secgroup:%s", name, network_name, subnet_name, vnic_type, sec_group_id)
        self.resources[name] = {
            'type': 'OS::Neutron::Port',
            'depends_on': [subnet_name],
            'properties': {
                'name': name,
                'binding:vnic_type': vnic_type,
                'fixed_ips': [{'subnet': {'get_resource': subnet_name}}],
                'network_id': {'get_resource': network_name},
                'replacement_policy': 'AUTO',
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

    def add_keypair(self, name, key_uuid):
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
                        get_short_key_uuid(key_uuid) + '.pub'),
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
                'description': "Group allowing icmp and upd/tcp on all ports",
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
                     'protocol': 'icmp'}
                ]
            }
        }

        self._template['outputs'][name] = {
            'description': 'ID of Security Group',
            'value': {'get_resource': name}
        }

    def add_server(self, name, image, flavor, flavors, ports=None,
                   networks=None, scheduler_hints=None, user=None,
                   key_name=None, user_data=None, metadata=None,
                   additional_properties=None):
        """add to the template a Nova Server"""
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

    HEAT_WAIT_LOOP_INTERVAL = 2
    HEAT_CREATE_COMPLETE_STATUS = u'CREATE_COMPLETE'

    def create(self, block=True, timeout=3600):
        """
        creates a template in the target cloud using heat
        returns a dict with the requested output values from the template

        :param block: Wait for Heat create to finish
        :type block: bool
        :param: timeout: timeout in seconds for Heat create, default 3600s
        :type timeout: int
        """
        log.info("Creating stack '%s'", self.name)

        # create stack early to support cleanup, e.g. ctrl-c while waiting
        stack = HeatStack(self.name)

        heat_client = self.heat_client
        start_time = time.time()
        stack.uuid = self.uuid = heat_client.stacks.create(
            stack_name=self.name, template=self._template,
            parameters=self.heat_parameters)['stack']['id']

        if not block:
            self.outputs = stack.outputs = {}
            end_time = time.time()
            log.info("Created stack '%s' in %.3e secs",
                     self.name, end_time - start_time)
            return stack

        time_limit = start_time + timeout
        for status in iter(self.status, self.HEAT_CREATE_COMPLETE_STATUS):
            log.debug("stack state %s", status)
            if status == u'CREATE_FAILED':
                stack_status_reason = heat_client.stacks.get(self.uuid).stack_status_reason
                heat_client.stacks.delete(self.uuid)
                raise RuntimeError(stack_status_reason)
            if time.time() > time_limit:
                raise RuntimeError("Heat stack create timeout")

            time.sleep(self.HEAT_WAIT_LOOP_INTERVAL)

        end_time = time.time()
        outputs = heat_client.stacks.get(self.uuid).outputs
        log.info("Created stack '%s' in %.3e secs",
                 self.name, end_time - start_time)

        # keep outputs as unicode
        self.outputs = {output["output_key"]: output["output_value"] for output
                        in outputs}

        stack.outputs = self.outputs
        return stack
