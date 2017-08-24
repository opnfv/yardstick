##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import

import os
import time
import sys
import logging

from keystoneauth1 import loading
from keystoneauth1 import session
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
    """Returns a creds dictionary filled with parsed from env"""
    creds = {}

    keystone_api_version = os.getenv('OS_IDENTITY_API_VERSION')

    if keystone_api_version is None or keystone_api_version == '2':
        keystone_v3 = False
        tenant_env = 'OS_TENANT_NAME'
        tenant = 'tenant_name'
    else:
        keystone_v3 = True
        tenant_env = 'OS_PROJECT_NAME'
        tenant = 'project_name'

    # The most common way to pass these info to the script is to do it
    # through environment variables.
    creds.update({
        "username": os.environ.get("OS_USERNAME"),
        "password": os.environ.get("OS_PASSWORD"),
        "auth_url": os.environ.get("OS_AUTH_URL"),
        tenant: os.environ.get(tenant_env)
    })

    if keystone_v3:
        if os.getenv('OS_USER_DOMAIN_NAME') is not None:
            creds.update({
                "user_domain_name": os.getenv('OS_USER_DOMAIN_NAME')
            })
        if os.getenv('OS_PROJECT_DOMAIN_NAME') is not None:
            creds.update({
                "project_domain_name": os.getenv('OS_PROJECT_DOMAIN_NAME')
            })

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


# *********************************************
#   NOVA
# *********************************************
def get_instances(nova_client):     # pragma: no cover
    try:
        return nova_client.servers.list(search_opts={'all_tenants': 1})
    except Exception:
        log.exception("Error [get_instances(nova_client)]")


def get_instance_status(nova_client, instance):     # pragma: no cover
    try:
        return nova_client.servers.get(instance.id).status
    except Exception:
        log.exception("Error [get_instance_status(nova_client)]")


def get_instance_by_name(nova_client, instance_name):   # pragma: no cover
    try:
        return nova_client.servers.find(name=instance_name)
    except Exception:
        log.exception("Error [get_instance_by_name(nova_client, '%s')]",
                      instance_name)


def get_aggregates(nova_client):    # pragma: no cover
    try:
        return nova_client.aggregates.list()
    except Exception:
        log.exception("Error [get_aggregates(nova_client)]")


def get_availability_zones(nova_client):    # pragma: no cover
    try:
        return nova_client.availability_zones.list()
    except Exception:
        log.exception("Error [get_availability_zones(nova_client)]")


def get_availability_zone_names(nova_client):   # pragma: no cover
    try:
        return [az.zoneName for az in get_availability_zones(nova_client)]
    except Exception:
        log.exception("Error [get_availability_zone_names(nova_client)]")


def create_aggregate(nova_client, aggregate_name, av_zone):  # pragma: no cover
    try:
        nova_client.aggregates.create(aggregate_name, av_zone)
    except Exception:
        log.exception("Error [create_aggregate(nova_client, %s, %s)]",
                      aggregate_name, av_zone)
        return False
    else:
        return True


def get_aggregate_id(nova_client, aggregate_name):      # pragma: no cover
    try:
        aggregates = get_aggregates(nova_client)
        _id = next((ag.id for ag in aggregates if ag.name == aggregate_name))
    except Exception:
        log.exception("Error [get_aggregate_id(nova_client, %s)]",
                      aggregate_name)
    else:
        return _id


def add_host_to_aggregate(nova_client, aggregate_name,
                          compute_host):    # pragma: no cover
    try:
        aggregate_id = get_aggregate_id(nova_client, aggregate_name)
        nova_client.aggregates.add_host(aggregate_id, compute_host)
    except Exception:
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
    except Exception:
        log.exception("Error [create_aggregate_with_host("
                      "nova_client, %s, %s, %s)]",
                      aggregate_name, av_zone, compute_host)
        return False
    else:
        return True


def create_keypair(nova_client, name, key_path=None):    # pragma: no cover
    try:
        with open(key_path) as fpubkey:
            keypair = get_nova_client().keypairs.create(name=name, public_key=fpubkey.read())
            return keypair
    except Exception:
        log.exception("Error [create_keypair(nova_client)]")


def create_instance(json_body):    # pragma: no cover
    try:
        return get_nova_client().servers.create(**json_body)
    except Exception:
        log.exception("Error create instance failed")
        return None


def create_instance_and_wait_for_active(json_body):    # pragma: no cover
    SLEEP = 3
    VM_BOOT_TIMEOUT = 180
    nova_client = get_nova_client()
    instance = create_instance(json_body)
    count = VM_BOOT_TIMEOUT / SLEEP
    for n in range(count, -1, -1):
        status = get_instance_status(nova_client, instance)
        if status.lower() == "active":
            return instance
        elif status.lower() == "error":
            log.error("The instance went to ERROR status.")
            return None
        time.sleep(SLEEP)
    log.error("Timeout booting the instance.")
    return None


def attach_server_volume(server_id, volume_id, device=None):    # pragma: no cover
    try:
        get_nova_client().volumes.create_server_volume(server_id, volume_id, device)
    except Exception:
        log.exception("Error [attach_server_volume(nova_client, '%s', '%s')]",
                      server_id, volume_id)
        return False
    else:
        return True


def delete_instance(nova_client, instance_id):      # pragma: no cover
    try:
        nova_client.servers.force_delete(instance_id)
    except Exception:
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
    except Exception:
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
    except Exception:
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
        return get_nova_client().flavors.create(name, ram, vcpus, disk, **kwargs)
    except Exception:
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
    for i in range(iterations):
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
    except Exception:
        log.exception("Error [delete_flavor(nova_client, %s)]", flavor_id)
        return False
    else:
        return True


def delete_keypair(nova_client, key):     # pragma: no cover
    try:
        nova_client.keypairs.delete(key=key)
        return True
    except Exception:
        log.exception("Error [delete_keypair(nova_client)]")
        return False


# *********************************************
#   NEUTRON
# *********************************************
def get_network_id(neutron_client, network_name):       # pragma: no cover
    networks = neutron_client.list_networks()['networks']
    return next((n['id'] for n in networks if n['name'] == network_name), None)


def get_port_id_by_ip(neutron_client, ip_address):      # pragma: no cover
    ports = neutron_client.list_ports()['ports']
    return next((i['id'] for i in ports for j in i.get(
        'fixed_ips') if j['ip_address'] == ip_address), None)


def create_neutron_net(neutron_client, json_body):      # pragma: no cover
    try:
        network = neutron_client.create_network(body=json_body)
        return network['network']['id']
    except Exception:
        log.error("Error [create_neutron_net(neutron_client)]")
        raise Exception("operation error")
        return None


def delete_neutron_net(neutron_client, network_id):      # pragma: no cover
    try:
        neutron_client.delete_network(network_id)
        return True
    except Exception:
        log.error("Error [delete_neutron_net(neutron_client, '%s')]" % network_id)
        return False


def create_neutron_subnet(neutron_client, json_body):      # pragma: no cover
    try:
        subnet = neutron_client.create_subnet(body=json_body)
        return subnet['subnets'][0]['id']
    except Exception:
        log.error("Error [create_neutron_subnet")
        raise Exception("operation error")
        return None


def create_neutron_router(neutron_client, json_body):      # pragma: no cover
    try:
        router = neutron_client.create_router(json_body)
        return router['router']['id']
    except Exception:
        log.error("Error [create_neutron_router(neutron_client)]")
        raise Exception("operation error")
        return None


def delete_neutron_router(neutron_client, router_id):      # pragma: no cover
    try:
        neutron_client.delete_router(router=router_id)
        return True
    except Exception:
        log.error("Error [delete_neutron_router(neutron_client, '%s')]" % router_id)
        return False


def remove_gateway_router(neutron_client, router_id):      # pragma: no cover
    try:
        neutron_client.remove_gateway_router(router_id)
        return True
    except Exception:
        log.error("Error [remove_gateway_router(neutron_client, '%s')]" % router_id)
        return False


def remove_interface_router(neutron_client, router_id, subnet_id,
                            **json_body):      # pragma: no cover
    json_body.update({"subnet_id": subnet_id})
    try:
        neutron_client.remove_interface_router(router=router_id,
                                               body=json_body)
        return True
    except Exception:
        log.error("Error [remove_interface_router(neutron_client, '%s', "
                  "'%s')]" % (router_id, subnet_id))
        return False


def create_floating_ip(neutron_client, extnet_id):      # pragma: no cover
    props = {'floating_network_id': extnet_id}
    try:
        ip_json = neutron_client.create_floatingip({'floatingip': props})
        fip_addr = ip_json['floatingip']['floating_ip_address']
        fip_id = ip_json['floatingip']['id']
    except Exception:
        log.error("Error [create_floating_ip(neutron_client)]")
        return None
    return {'fip_addr': fip_addr, 'fip_id': fip_id}


def delete_floating_ip(nova_client, floatingip_id):      # pragma: no cover
    try:
        nova_client.floating_ips.delete(floatingip_id)
        return True
    except Exception:
        log.error("Error [delete_floating_ip(nova_client, '%s')]" % floatingip_id)
        return False


def get_security_groups(neutron_client):      # pragma: no cover
    try:
        security_groups = neutron_client.list_security_groups()[
            'security_groups']
        return security_groups
    except Exception:
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


def create_security_group(neutron_client, sg_name, sg_description):      # pragma: no cover
    json_body = {'security_group': {'name': sg_name,
                                    'description': sg_description}}
    try:
        secgroup = neutron_client.create_security_group(json_body)
        return secgroup['security_group']
    except Exception:
        log.error("Error [create_security_group(neutron_client, '%s', "
                  "'%s')]" % (sg_name, sg_description))
        return None


def create_secgroup_rule(neutron_client, sg_id, direction, protocol,
                         port_range_min=None, port_range_max=None,
                         **json_body):      # pragma: no cover
    # We create a security group in 2 steps
    # 1 - we check the format and set the json body accordingly
    # 2 - we call neturon client to create the security group

    # Format check
    json_body.update({'security_group_rule': {'direction': direction,
                     'security_group_id': sg_id, 'protocol': protocol}})
    # parameters may be
    # - both None => we do nothing
    # - both Not None => we add them to the json description
    # but one cannot be None is the other is not None
    if (port_range_min is not None and port_range_max is not None):
        # add port_range in json description
        json_body['security_group_rule']['port_range_min'] = port_range_min
        json_body['security_group_rule']['port_range_max'] = port_range_max
        log.debug("Security_group format set (port range included)")
    else:
        # either both port range are set to None => do nothing
        # or one is set but not the other => log it and return False
        if port_range_min is None and port_range_max is None:
            log.debug("Security_group format set (no port range mentioned)")
        else:
            log.error("Bad security group format."
                      "One of the port range is not properly set:"
                      "range min: {},"
                      "range max: {}".format(port_range_min,
                                             port_range_max))
            return False

    # Create security group using neutron client
    try:
        neutron_client.create_security_group_rule(json_body)
        return True
    except Exception:
        log.exception("Impossible to create_security_group_rule,"
                      "security group rule probably already exists")
        return False


def create_security_group_full(neutron_client,
                               sg_name, sg_description):      # pragma: no cover
    sg_id = get_security_group_id(neutron_client, sg_name)
    if sg_id != '':
        log.info("Using existing security group '%s'..." % sg_name)
    else:
        log.info("Creating security group  '%s'..." % sg_name)
        SECGROUP = create_security_group(neutron_client,
                                         sg_name,
                                         sg_description)
        if not SECGROUP:
            log.error("Failed to create the security group...")
            return None

        sg_id = SECGROUP['id']

        log.debug("Security group '%s' with ID=%s created successfully."
                  % (SECGROUP['name'], sg_id))

        log.debug("Adding ICMP rules in security group '%s'..."
                  % sg_name)
        if not create_secgroup_rule(neutron_client, sg_id,
                                    'ingress', 'icmp'):
            log.error("Failed to create the security group rule...")
            return None

        log.debug("Adding SSH rules in security group '%s'..."
                  % sg_name)
        if not create_secgroup_rule(
                neutron_client, sg_id, 'ingress', 'tcp', '22', '22'):
            log.error("Failed to create the security group rule...")
            return None

        if not create_secgroup_rule(
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
        log.error("Error: file %s does not exist." % file_path)
        return None
    try:
        image_id = get_image_id(glance_client, image_name)
        if image_id is not None:
            log.info("Image %s already exists." % image_name)
        else:
            log.info("Creating image '%s' from '%s'...", image_name, file_path)

            image = glance_client.images.create(name=image_name,
                                                visibility=public,
                                                disk_format=disk_format,
                                                container_format=container_format,
                                                min_disk=min_disk,
                                                min_ram=min_ram,
                                                tags=tag,
                                                protected=protected,
                                                **kwargs)
            image_id = image.id
            with open(file_path) as image_data:
                glance_client.images.upload(image_id, image_data)
        return image_id
    except Exception:
        log.error("Error [create_glance_image(glance_client, '%s', '%s', '%s')]",
                  image_name, file_path, public)
        return None


def delete_image(glance_client, image_id):    # pragma: no cover
    try:
        glance_client.images.delete(image_id)

    except Exception:
        log.exception("Error [delete_flavor(glance_client, %s)]", image_id)
        return False
    else:
        return True


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
    except Exception:
        log.exception("Error [create_volume(cinder_client, %s)]",
                      (volume_name, volume_size))
        return None


def delete_volume(cinder_client, volume_id, forced=False):      # pragma: no cover
    try:
        if forced:
            try:
                cinder_client.volumes.detach(volume_id)
            except:
                log.error(sys.exc_info()[0])
            cinder_client.volumes.force_delete(volume_id)
        else:
            while True:
                volume = get_cinder_client().volumes.get(volume_id)
                if volume.status.lower() == 'available':
                    break
            cinder_client.volumes.delete(volume_id)
        return True
    except Exception:
        log.exception("Error [delete_volume(cinder_client, '%s')]" % volume_id)
        return False


def detach_volume(server_id, volume_id):      # pragma: no cover
    try:
        get_nova_client().volumes.delete_server_volume(server_id, volume_id)
        return True
    except Exception:
        log.exception("Error [detach_server_volume(nova_client, '%s', '%s')]",
                      server_id, volume_id)
        return False
