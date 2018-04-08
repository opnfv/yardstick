##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import os
import time
import sys
import logging

from keystoneauth1 import loading
from keystoneauth1 import session
import shade
from shade import exc

from cinderclient import client as cinderclient
from novaclient import client as novaclient
from glanceclient import client as glanceclient
from neutronclient.neutron import client as neutronclient


log = logging.getLogger(__name__)

DEFAULT_HEAT_API_VERSION = '1'
DEFAULT_API_VERSION = '2'


# *********************************************
#   CREDENTIALS
# *********************************************
def get_credentials():
    """Returns a creds dictionary filled with parsed from env

    Keystone API version used is 3; v2 was deprecated in 2014 (Icehouse). Along
    with this deprecation, environment variable 'OS_TENANT_NAME' is replaced by
    'OS_PROJECT_NAME'.
    """
    creds = {'username': os.environ.get('OS_USERNAME'),
             'password': os.environ.get('OS_PASSWORD'),
             'auth_url': os.environ.get('OS_AUTH_URL'),
             'project_name': os.environ.get('OS_PROJECT_NAME')
             }

    if os.getenv('OS_USER_DOMAIN_NAME'):
        creds['user_domain_name'] = os.getenv('OS_USER_DOMAIN_NAME')
    if os.getenv('OS_PROJECT_DOMAIN_NAME'):
        creds['project_domain_name'] = os.getenv('OS_PROJECT_DOMAIN_NAME')

    return creds


def get_session_auth():
    loader = loading.get_plugin_loader('password')
    creds = get_credentials()
    auth = loader.load_from_options(**creds)
    return auth


def get_session():
    auth = get_session_auth()
    try:
        cacert = os.environ['OS_CACERT']
    except KeyError:
        return session.Session(auth=auth)
    else:
        insecure = os.getenv('OS_INSECURE', '').lower() == 'true'
        cacert = False if insecure else cacert
        return session.Session(auth=auth, verify=cacert)


def get_endpoint(service_type, endpoint_type='publicURL'):
    auth = get_session_auth()
    # for multi-region, we need to specify region
    # when finding the endpoint
    return get_session().get_endpoint(auth=auth,
                                      service_type=service_type,
                                      endpoint_type=endpoint_type,
                                      region_name=os.environ.get(
                                          "OS_REGION_NAME"))


# *********************************************
#   CLIENTS
# *********************************************
def get_heat_api_version():     # pragma: no cover
    try:
        api_version = os.environ['HEAT_API_VERSION']
    except KeyError:
        return DEFAULT_HEAT_API_VERSION
    else:
        log.info("HEAT_API_VERSION is set in env as '%s'", api_version)
        return api_version


def get_cinder_client_version():      # pragma: no cover
    try:
        api_version = os.environ['OS_VOLUME_API_VERSION']
    except KeyError:
        return DEFAULT_API_VERSION
    else:
        log.info("OS_VOLUME_API_VERSION is set in env as '%s'", api_version)
        return api_version


def get_cinder_client():      # pragma: no cover
    sess = get_session()
    return cinderclient.Client(get_cinder_client_version(), session=sess)


def get_nova_client_version():      # pragma: no cover
    try:
        api_version = os.environ['OS_COMPUTE_API_VERSION']
    except KeyError:
        return DEFAULT_API_VERSION
    else:
        log.info("OS_COMPUTE_API_VERSION is set in env as '%s'", api_version)
        return api_version


def get_nova_client():      # pragma: no cover
    sess = get_session()
    return novaclient.Client(get_nova_client_version(), session=sess)


def get_neutron_client_version():   # pragma: no cover
    try:
        api_version = os.environ['OS_NETWORK_API_VERSION']
    except KeyError:
        return DEFAULT_API_VERSION
    else:
        log.info("OS_NETWORK_API_VERSION is set in env as '%s'", api_version)
        return api_version


def get_neutron_client():   # pragma: no cover
    sess = get_session()
    return neutronclient.Client(get_neutron_client_version(), session=sess)


def get_glance_client_version():    # pragma: no cover
    try:
        api_version = os.environ['OS_IMAGE_API_VERSION']
    except KeyError:
        return DEFAULT_API_VERSION
    else:
        log.info("OS_IMAGE_API_VERSION is set in env as '%s'", api_version)
        return api_version


def get_glance_client():    # pragma: no cover
    sess = get_session()
    return glanceclient.Client(get_glance_client_version(), session=sess)


def get_shade_client():
    return shade.openstack_cloud()


# *********************************************
#   NOVA
# *********************************************
def get_instances(nova_client):
    try:
        return nova_client.servers.list(search_opts={'all_tenants': 1})
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_instances(nova_client)]")


def get_instance_status(nova_client, instance):     # pragma: no cover
    try:
        return nova_client.servers.get(instance.id).status
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_instance_status(nova_client)]")


def get_instance_by_name(nova_client, instance_name):   # pragma: no cover
    try:
        return nova_client.servers.find(name=instance_name)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_instance_by_name(nova_client, '%s')]",
                      instance_name)


def get_aggregates(nova_client):    # pragma: no cover
    try:
        return nova_client.aggregates.list()
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_aggregates(nova_client)]")


def get_availability_zones(nova_client):    # pragma: no cover
    try:
        return nova_client.availability_zones.list()
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_availability_zones(nova_client)]")


def get_availability_zone_names(nova_client):   # pragma: no cover
    try:
        return [az.zoneName for az in get_availability_zones(nova_client)]
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_availability_zone_names(nova_client)]")


def create_aggregate(nova_client, aggregate_name, av_zone):  # pragma: no cover
    try:
        nova_client.aggregates.create(aggregate_name, av_zone)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [create_aggregate(nova_client, %s, %s)]",
                      aggregate_name, av_zone)
        return False
    else:
        return True


def get_aggregate_id(nova_client, aggregate_name):      # pragma: no cover
    try:
        aggregates = get_aggregates(nova_client)
        _id = next((ag.id for ag in aggregates if ag.name == aggregate_name))
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [get_aggregate_id(nova_client, %s)]",
                      aggregate_name)
    else:
        return _id


def add_host_to_aggregate(nova_client, aggregate_name,
                          compute_host):    # pragma: no cover
    try:
        aggregate_id = get_aggregate_id(nova_client, aggregate_name)
        nova_client.aggregates.add_host(aggregate_id, compute_host)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [add_host_to_aggregate(nova_client, %s, %s)]",
                      aggregate_name, compute_host)
        return False
    else:
        return True


def create_aggregate_with_host(nova_client, aggregate_name, av_zone,
                               compute_host):    # pragma: no cover
    try:
        create_aggregate(nova_client, aggregate_name, av_zone)
        add_host_to_aggregate(nova_client, aggregate_name, compute_host)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [create_aggregate_with_host("
                      "nova_client, %s, %s, %s)]",
                      aggregate_name, av_zone, compute_host)
        return False
    else:
        return True


def create_keypair(name, key_path=None):    # pragma: no cover
    try:
        with open(key_path) as fpubkey:
            keypair = get_nova_client().keypairs.create(
                name=name, public_key=fpubkey.read())
            return keypair
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [create_keypair(nova_client)]")


def create_instance(json_body):    # pragma: no cover
    try:
        return get_nova_client().servers.create(**json_body)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error create instance failed")
        return None


def create_instance_and_wait_for_active(json_body):    # pragma: no cover
    SLEEP = 3
    VM_BOOT_TIMEOUT = 180
    nova_client = get_nova_client()
    instance = create_instance(json_body)
    for _ in range(int(VM_BOOT_TIMEOUT / SLEEP)):
        status = get_instance_status(nova_client, instance)
        if status.lower() == "active":
            return instance
        elif status.lower() == "error":
            log.error("The instance went to ERROR status.")
            return None
        time.sleep(SLEEP)
    log.error("Timeout booting the instance.")
    return None


def attach_server_volume(server_id, volume_id,
                         device=None):    # pragma: no cover
    try:
        get_nova_client().volumes.create_server_volume(server_id,
                                                       volume_id, device)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [attach_server_volume(nova_client, '%s', '%s')]",
                      server_id, volume_id)
        return False
    else:
        return True


def delete_instance(nova_client, instance_id):      # pragma: no cover
    try:
        nova_client.servers.force_delete(instance_id)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [delete_instance(nova_client, '%s')]",
                      instance_id)
        return False
    else:
        return True


def remove_host_from_aggregate(nova_client, aggregate_name,
                               compute_host):  # pragma: no cover
    try:
        aggregate_id = get_aggregate_id(nova_client, aggregate_name)
        nova_client.aggregates.remove_host(aggregate_id, compute_host)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error remove_host_from_aggregate(nova_client, %s, %s)",
                      aggregate_name, compute_host)
        return False
    else:
        return True


def remove_hosts_from_aggregate(nova_client,
                                aggregate_name):   # pragma: no cover
    aggregate_id = get_aggregate_id(nova_client, aggregate_name)
    hosts = nova_client.aggregates.get(aggregate_id).hosts
    assert(
        all(remove_host_from_aggregate(nova_client, aggregate_name, host)
            for host in hosts))


def delete_aggregate(nova_client, aggregate_name):  # pragma: no cover
    try:
        remove_hosts_from_aggregate(nova_client, aggregate_name)
        nova_client.aggregates.delete(aggregate_name)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [delete_aggregate(nova_client, %s)]",
                      aggregate_name)
        return False
    else:
        return True


def get_server_by_name(name):   # pragma: no cover
    try:
        return get_nova_client().servers.list(search_opts={'name': name})[0]
    except IndexError:
        log.exception('Failed to get nova client')
        raise


def create_flavor(name, ram, vcpus, disk, **kwargs):   # pragma: no cover
    try:
        return get_nova_client().flavors.create(name, ram, vcpus,
                                                disk, **kwargs)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [create_flavor(nova_client, %s, %s, %s, %s, %s)]",
                      name, ram, disk, vcpus, kwargs['is_public'])
        return None


def get_image_by_name(name):    # pragma: no cover
    images = get_nova_client().images.list()
    try:
        return next((a for a in images if a.name == name))
    except StopIteration:
        log.exception('No image matched')


def get_flavor_id(nova_client, flavor_name):    # pragma: no cover
    flavors = nova_client.flavors.list(detailed=True)
    flavor_id = ''
    for f in flavors:
        if f.name == flavor_name:
            flavor_id = f.id
            break
    return flavor_id


def get_flavor_by_name(name):   # pragma: no cover
    flavors = get_nova_client().flavors.list()
    try:
        return next((a for a in flavors if a.name == name))
    except StopIteration:
        log.exception('No flavor matched')


def check_status(status, name, iterations, interval):   # pragma: no cover
    for _ in range(iterations):
        try:
            server = get_server_by_name(name)
        except IndexError:
            log.error('Cannot found %s server', name)
            raise

        if server.status == status:
            return True

        time.sleep(interval)
    return False


def delete_flavor(flavor_id):    # pragma: no cover
    try:
        get_nova_client().flavors.delete(flavor_id)
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [delete_flavor(nova_client, %s)]", flavor_id)
        return False
    else:
        return True


def delete_keypair(nova_client, key):     # pragma: no cover
    try:
        nova_client.keypairs.delete(key=key)
        return True
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [delete_keypair(nova_client)]")
        return False


# *********************************************
#   NEUTRON
# *********************************************
def create_neutron_net(shade_client, network_name, shared=False,
                       admin_state_up=True, external=False, provider=None,
                       project_id=None):
    """Create a neutron network.

    :param network_name:(string) name of the network being created.
    :param shared:(bool) whether the network is shared.
    :param admin_state_up:(bool) set the network administrative state.
    :param external:(bool) whether this network is externally accessible.
    :param provider:(dict) a dict of network provider options.
    :param project_id:(string) specify the project ID this network
                      will be created on (admin-only).
    :returns:(string) the network id.
    """
    try:
        networks = shade_client.create_network(
            name=network_name, shared=shared, admin_state_up=admin_state_up,
            external=external, provider=provider, project_id=project_id)
        return networks['id']
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [create_neutron_net(shade_client)]."
                  "Exception message, '%s'", o_exc.orig_message)
        return None


def delete_neutron_net(shade_client, network_id):
    try:
        return shade_client.delete_network(network_id)
    except exc.OpenStackCloudException:
        log.error("Error [delete_neutron_net(shade_client, '%s')]", network_id)
        return False


def create_neutron_subnet(shade_client, network_name_or_id, cidr=None,
                          ip_version=4, enable_dhcp=False, subnet_name=None,
                          tenant_id=None, allocation_pools=None,
                          gateway_ip=None, disable_gateway_ip=False,
                          dns_nameservers=None, host_routes=None,
                          ipv6_ra_mode=None, ipv6_address_mode=None,
                          use_default_subnetpool=False):
    """Create a subnet on a specified network.

    :param network_name_or_id:(string) the unique name or ID of the
                              attached network. If a non-unique name is
                              supplied, an exception is raised.
    :param cidr:(string) the CIDR.
    :param ip_version:(int) the IP version.
    :param enable_dhcp:(bool) whether DHCP is enable.
    :param subnet_name:(string) the name of the subnet.
    :param tenant_id:(string) the ID of the tenant who owns the network.
    :param allocation_pools: A list of dictionaries of the start and end
                            addresses for the allocation pools.
    :param gateway_ip:(string) the gateway IP address.
    :param disable_gateway_ip:(bool) whether gateway IP address is enabled.
    :param dns_nameservers: A list of DNS name servers for the subnet.
    :param host_routes: A list of host route dictionaries for the subnet.
    :param ipv6_ra_mode:(string) IPv6 Router Advertisement mode.
                        Valid values are: 'dhcpv6-stateful',
                        'dhcpv6-stateless', or 'slaac'.
    :param ipv6_address_mode:(string) IPv6 address mode.
                             Valid values are: 'dhcpv6-stateful',
                             'dhcpv6-stateless', or 'slaac'.
    :param use_default_subnetpool:(bool) use the default subnetpool for
                                  ``ip_version`` to obtain a CIDR. It is
                                  required to pass ``None`` to the ``cidr``
                                  argument when enabling this option.
    :returns:(string) the subnet id.
    """
    try:
        subnet = shade_client.create_subnet(
            network_name_or_id, cidr=cidr, ip_version=ip_version,
            enable_dhcp=enable_dhcp, subnet_name=subnet_name,
            tenant_id=tenant_id, allocation_pools=allocation_pools,
            gateway_ip=gateway_ip, disable_gateway_ip=disable_gateway_ip,
            dns_nameservers=dns_nameservers, host_routes=host_routes,
            ipv6_ra_mode=ipv6_ra_mode, ipv6_address_mode=ipv6_address_mode,
            use_default_subnetpool=use_default_subnetpool)
        return subnet['id']
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [create_neutron_subnet(shade_client)]. "
                  "Exception message: %s", o_exc.orig_message)
        return None


def create_neutron_router(shade_client, name=None, admin_state_up=True,
                          ext_gateway_net_id=None, enable_snat=None,
                          ext_fixed_ips=None, project_id=None):
    """Create a logical router.

    :param name:(string) the router name.
    :param admin_state_up:(bool) the administrative state of the router.
    :param ext_gateway_net_id:(string) network ID for the external gateway.
    :param enable_snat:(bool) enable Source NAT (SNAT) attribute.
    :param ext_fixed_ips: List of dictionaries of desired IP and/or subnet
                          on the external network.
    :param project_id:(string) project ID for the router.

    :returns:(string) the router id.
    """
    try:
        router = shade_client.create_router(
            name, admin_state_up, ext_gateway_net_id, enable_snat,
            ext_fixed_ips, project_id)
        return router['id']
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [create_neutron_router(shade_client)]. "
                  "Exception message: %s", o_exc.orig_message)


def delete_neutron_router(shade_client, router_id):
    try:
        return shade_client.delete_router(router_id)
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [delete_neutron_router(shade_client, '%s')]. "
                  "Exception message: %s", router_id, o_exc.orig_message)
        return False


def remove_gateway_router(neutron_client, router_id):      # pragma: no cover
    try:
        neutron_client.remove_gateway_router(router_id)
        return True
    except Exception:  # pylint: disable=broad-except
        log.error("Error [remove_gateway_router(neutron_client, '%s')]",
                  router_id)
        return False


def remove_router_interface(shade_client, router, subnet_id=None,
                            port_id=None):
    """Detach a subnet from an internal router interface.

    At least one of subnet_id or port_id must be supplied. If you specify both
    subnet and port ID, the subnet ID must correspond to the subnet ID of the
    first IP address on the port specified by the port ID.
    Otherwise an error occurs.

    :param router: The dict object of the router being changed
    :param subnet_id:(string) The ID of the subnet to use for the interface
    :param port_id:(string) The ID of the port to use for the interface
    :returns: True on success
    """
    try:
        shade_client.remove_router_interface(
            router, subnet_id=subnet_id, port_id=port_id)
        return True
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [remove_interface_router(shade_client)]. "
                  "Exception message: %s", o_exc.orig_message)
        return False


def create_floating_ip(shade_client, network_name_or_id=None, server=None,
                       fixed_address=None, nat_destination=None,
                       port=None, wait=False, timeout=60):
    """Allocate a new floating IP from a network or a pool.

    :param network_name_or_id: Name or ID of the network
                               that the floating IP should come from.
    :param server: Server dict for the server to create
                  the IP for and to which it should be attached.
    :param fixed_address: Fixed IP to attach the floating ip to.
    :param nat_destination: Name or ID of the network
                           that the fixed IP to attach the floating
                           IP to should be on.
    :param port: The port ID that the floating IP should be
                attached to. Specifying a port conflicts with specifying a
                server,fixed_address or nat_destination.
    :param wait: Whether to wait for the IP to be active.Only applies
                if a server is provided.
    :param timeout: How long to wait for the IP to be active.Only
                   applies if a server is provided.

    :returns:Floating IP id and address
    """
    try:
        fip = shade_client.create_floating_ip(
            network=network_name_or_id, server=server,
            fixed_address=fixed_address, nat_destination=nat_destination,
            port=port, wait=wait, timeout=timeout)
        return {'fip_addr': fip['floating_ip_address'], 'fip_id': fip['id']}
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [create_floating_ip(shade_client)]. "
                  "Exception message: %s", o_exc.orig_message)


def delete_floating_ip(shade_client, floating_ip_id, retry=1):
    try:
        return shade_client.delete_floating_ip(floating_ip_id=floating_ip_id,
                                               retry=retry)
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [delete_floating_ip(shade_client,'%s')]. "
                  "Exception message: %s", floating_ip_id, o_exc.orig_message)
        return False


def get_security_groups(neutron_client):      # pragma: no cover
    try:
        security_groups = neutron_client.list_security_groups()[
            'security_groups']
        return security_groups
    except Exception:  # pylint: disable=broad-except
        log.error("Error [get_security_groups(neutron_client)]")
        return None


def get_security_group_id(neutron_client, sg_name):      # pragma: no cover
    security_groups = get_security_groups(neutron_client)
    id = ''
    for sg in security_groups:
        if sg['name'] == sg_name:
            id = sg['id']
            break
    return id


def create_security_group(neutron_client, sg_name,
                          sg_description):      # pragma: no cover
    json_body = {'security_group': {'name': sg_name,
                                    'description': sg_description}}
    try:
        secgroup = neutron_client.create_security_group(json_body)
        return secgroup['security_group']
    except Exception:  # pylint: disable=broad-except
        log.error("Error [create_security_group(neutron_client, '%s', "
                  "'%s')]", sg_name, sg_description)
        return None


def create_security_group_rule(shade_client, secgroup_name_or_id,
                               port_range_min=None, port_range_max=None,
                               protocol=None, remote_ip_prefix=None,
                               remote_group_id=None, direction='ingress',
                               ethertype='IPv4', project_id=None):
    """Create a new security group rule

    :param secgroup_name_or_id:(string) The security group name or ID to
                               associate with this security group rule. If a
                               non-unique group name is given, an exception is
                               raised.
    :param port_range_min:(int) The minimum port number in the range that is
                          matched by the security group rule. If the protocol
                          is TCP or UDP, this value must be less than or equal
                          to the port_range_max attribute value. If nova is
                          used by the cloud provider for security groups, then
                          a value of None will be transformed to -1.
    :param port_range_max:(int) The maximum port number in the range that is
                          matched by the security group rule. The
                          port_range_min attribute constrains the
                          port_range_max attribute. If nova is used by the
                          cloud provider for security groups, then a value of
                          None will be transformed to -1.
    :param protocol:(string) The protocol that is matched by the security group
                    rule. Valid values are None, tcp, udp, and icmp.
    :param remote_ip_prefix:(string) The remote IP prefix to be associated with
                            this security group rule. This attribute matches
                            the specified IP prefix as the source IP address of
                            the IP packet.
    :param remote_group_id:(string) The remote group ID to be associated with
                           this security group rule.
    :param direction:(string) Ingress or egress: The direction in which the
                     security group rule is applied.
    :param ethertype:(string) Must be IPv4 or IPv6, and addresses represented
                     in CIDR must match the ingress or egress rules.
    :param project_id:(string) Specify the project ID this security group will
                      be created on (admin-only).

    :returns: True on success.
    """

    try:
        shade_client.create_security_group_rule(
            secgroup_name_or_id, port_range_min=port_range_min,
            port_range_max=port_range_max, protocol=protocol,
            remote_ip_prefix=remote_ip_prefix, remote_group_id=remote_group_id,
            direction=direction, ethertype=ethertype, project_id=project_id)
        return True
    except exc.OpenStackCloudException as op_exc:
        log.error("Failed to create_security_group_rule(shade_client). "
                  "Exception message: %s", op_exc.orig_message)
        return False


def create_security_group_full(neutron_client, sg_name,
                               sg_description):      # pragma: no cover
    sg_id = get_security_group_id(neutron_client, sg_name)
    if sg_id != '':
        log.info("Using existing security group '%s'...", sg_name)
    else:
        log.info("Creating security group  '%s'...", sg_name)
        SECGROUP = create_security_group(neutron_client,
                                         sg_name,
                                         sg_description)
        if not SECGROUP:
            log.error("Failed to create the security group...")
            return None

        sg_id = SECGROUP['id']

        log.debug("Security group '%s' with ID=%s created successfully.",
                  SECGROUP['name'], sg_id)

        log.debug("Adding ICMP rules in security group '%s'...", sg_name)
        if not create_security_group_rule(neutron_client, sg_id,
                                          'ingress', 'icmp'):
            log.error("Failed to create the security group rule...")
            return None

        log.debug("Adding SSH rules in security group '%s'...", sg_name)
        if not create_security_group_rule(
                neutron_client, sg_id, 'ingress', 'tcp', '22', '22'):
            log.error("Failed to create the security group rule...")
            return None

        if not create_security_group_rule(
                neutron_client, sg_id, 'egress', 'tcp', '22', '22'):
            log.error("Failed to create the security group rule...")
            return None
    return sg_id


# *********************************************
#   GLANCE
# *********************************************
def get_image_id(glance_client, image_name):    # pragma: no cover
    images = glance_client.images.list()
    return next((i.id for i in images if i.name == image_name), None)


def create_image(glance_client, image_name, file_path, disk_format,
                 container_format, min_disk, min_ram, protected, tag,
                 public, **kwargs):    # pragma: no cover
    if not os.path.isfile(file_path):
        log.error("Error: file %s does not exist.", file_path)
        return None
    try:
        image_id = get_image_id(glance_client, image_name)
        if image_id is not None:
            log.info("Image %s already exists.", image_name)
        else:
            log.info("Creating image '%s' from '%s'...", image_name, file_path)

            image = glance_client.images.create(
                name=image_name, visibility=public, disk_format=disk_format,
                container_format=container_format, min_disk=min_disk,
                min_ram=min_ram, tags=tag, protected=protected, **kwargs)
            image_id = image.id
            with open(file_path) as image_data:
                glance_client.images.upload(image_id, image_data)
        return image_id
    except Exception:  # pylint: disable=broad-except
        log.error(
            "Error [create_glance_image(glance_client, '%s', '%s', '%s')]",
            image_name, file_path, public)
        return None


def delete_image(glance_client, image_id):    # pragma: no cover
    try:
        glance_client.images.delete(image_id)

    except Exception:  # pylint: disable=broad-except
        log.exception("Error [delete_flavor(glance_client, %s)]", image_id)
        return False
    else:
        return True


def list_images(shade_client=None):
    if shade_client is None:
        shade_client = get_shade_client()

    try:
        return shade_client.list_images()
    except exc.OpenStackCloudException as o_exc:
        log.error("Error [list_images(shade_client)]."
                  "Exception message, '%s'", o_exc.orig_message)
        return False


# *********************************************
#   CINDER
# *********************************************
def get_volume_id(volume_name):    # pragma: no cover
    volumes = get_cinder_client().volumes.list()
    return next((v.id for v in volumes if v.name == volume_name), None)


def create_volume(cinder_client, volume_name, volume_size,
                  volume_image=False):    # pragma: no cover
    try:
        if volume_image:
            volume = cinder_client.volumes.create(name=volume_name,
                                                  size=volume_size,
                                                  imageRef=volume_image)
        else:
            volume = cinder_client.volumes.create(name=volume_name,
                                                  size=volume_size)
        return volume
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [create_volume(cinder_client, %s)]",
                      (volume_name, volume_size))
        return None


def delete_volume(cinder_client, volume_id,
                  forced=False):      # pragma: no cover
    try:
        if forced:
            try:
                cinder_client.volumes.detach(volume_id)
            except Exception:  # pylint: disable=broad-except
                log.error(sys.exc_info()[0])
            cinder_client.volumes.force_delete(volume_id)
        else:
            while True:
                volume = get_cinder_client().volumes.get(volume_id)
                if volume.status.lower() == 'available':
                    break
            cinder_client.volumes.delete(volume_id)
        return True
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [delete_volume(cinder_client, '%s')]", volume_id)
        return False


def detach_volume(server_id, volume_id):      # pragma: no cover
    try:
        get_nova_client().volumes.delete_server_volume(server_id, volume_id)
        return True
    except Exception:  # pylint: disable=broad-except
        log.exception("Error [detach_server_volume(nova_client, '%s', '%s')]",
                      server_id, volume_id)
        return False
