##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import print_function
from __future__ import absolute_import
import os
from novaclient import client as novaclient
from neutronclient.v2_0 import client as neutronclient


def get_credentials(service):  # pragma: no cover
    """Returns a creds dictionary filled with the following keys:
    * username
    * password/api_key (depending on the service)
    * tenant_name/project_id (depending on the service)
    * auth_url
    :param service: a string indicating the name of the service
                    requesting the credentials.
    """
    creds = {}
    # Unfortunately, each of the OpenStack client will request slightly
    # different entries in their credentials dict.
    if service.lower() in ("nova", "cinder"):
        password = "api_key"
        tenant = "project_id"
    else:
        password = "password"
        tenant = "tenant_name"

    # The most common way to pass these info to the script is to do it through
    # environment variables.
    creds.update({
        "username": os.environ.get('OS_USERNAME', "admin"),
        password: os.environ.get("OS_PASSWORD", 'admin'),
        "auth_url": os.environ.get("OS_AUTH_URL"),
        tenant: os.environ.get("OS_TENANT_NAME", "admin"),
    })
    cacert = os.environ.get("OS_CACERT")
    if cacert is not None:
        # each openstack client uses differnt kwargs for this
        creds.update({"cacert": cacert,
                      "ca_cert": cacert,
                      "https_ca_cert": cacert,
                      "https_cacert": cacert,
                      "ca_file": cacert})
        creds.update({"insecure": "True", "https_insecure": "True"})
        if not os.path.isfile(cacert):
            print(("WARNING: The 'OS_CACERT' environment variable is " +
                   "set to %s but the file does not exist." % cacert))
    return creds


def get_instances(nova_client):  # pragma: no cover
    try:
        instances = nova_client.servers.list(search_opts={'all_tenants': 1})
        return instances
    except Exception as e:
        print("Error [get_instances(nova_client)]:", e)
        return None


def get_SFs(nova_client):  # pragma: no cover
    try:
        instances = get_instances(nova_client)
        SFs = []
        for instance in instances:
            if "sfc_test" not in instance.name:
                SFs.append(instance)
        return SFs
    except Exception as e:
        print("Error [get_SFs(nova_client)]:", e)
        return None


def get_external_net_id(neutron_client):  # pragma: no cover
    for network in neutron_client.list_networks()['networks']:
        if network['router:external']:
            return network['id']
    return False


def create_floating_ips(neutron_client):  # pragma: no cover
    extnet_id = get_external_net_id(neutron_client)
    ips = []
    props = {'floating_network_id': extnet_id}
    try:
        while len(ips) < 2:
            ip_json = neutron_client.create_floatingip({'floatingip': props})
            fip_addr = ip_json['floatingip']['floating_ip_address']
            ips.append(fip_addr)
    except Exception as e:
        print("Error [create_floating_ip(neutron_client)]:", e)
        return None
    return ips


def floatIPtoSFs(SFs, floatips):  # pragma: no cover
    try:
        i = 0
        for SF in SFs:
            SF.add_floating_ip(floatips[i])
            i = i + 1
        return True
    except Exception as e:
        print(("Error [add_floating_ip(nova_client, '%s', '%s')]:" %
               (SF, floatips[i]), e))
        return False


def get_an_IP():  # pragma: no cover

    creds_nova = get_credentials("nova")
    nova_client = novaclient.Client(version='2', **creds_nova)
    creds_neutron = get_credentials("neutron")
    neutron_client = neutronclient.Client(**creds_neutron)
    SFs = get_SFs(nova_client)
    floatips = create_floating_ips(neutron_client)
    floatIPtoSFs(SFs, floatips)
    return floatips


if __name__ == '__main__':  # pragma: no cover
    get_an_IP()
