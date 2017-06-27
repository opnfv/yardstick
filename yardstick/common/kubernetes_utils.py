##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from kubernetes import client
from kubernetes import config
from kubernetes.client.rest import ApiException

from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def get_core_api():     # pragma: no cover
    try:
        config.load_kube_config(config_file=consts.K8S_CONF_FILE)
    except IOError:
        LOG.exception('config file not found')
        raise

    return client.CoreV1Api()


def create_replication_controller(template,
                                  namespace='default',
                                  wait=False,
                                  **kwargs):    # pragma: no cover

    core_v1_api = get_core_api()
    try:
        core_v1_api.create_namespaced_replication_controller(namespace,
                                                             template,
                                                             **kwargs)
    except ApiException:
        LOG.exception('Create replication controller failed')
        raise


def delete_replication_controller(name,
                                  namespace='default',
                                  wait=False,
                                  **kwargs):    # pragma: no cover

    core_v1_api = get_core_api()
    body = kwargs.get('body', client.V1DeleteOptions())
    kwargs.pop('body', None)
    try:
        core_v1_api.delete_namespaced_replication_controller(name,
                                                             namespace,
                                                             body,
                                                             **kwargs)
    except ApiException:
        LOG.exception('Delete replication controller failed')
        raise


def delete_pod(name,
               namespace='default',
               wait=False,
               **kwargs):    # pragma: no cover

    core_v1_api = get_core_api()
    body = kwargs.get('body', client.V1DeleteOptions())
    kwargs.pop('body', None)
    try:
        core_v1_api.delete_namespaced_pod(name,
                                          namespace,
                                          body,
                                          **kwargs)
    except ApiException:
        LOG.exception('Delete pod failed')
        raise


def read_pod(name,
             namespace='default',
             **kwargs):  # pragma: no cover
    core_v1_api = get_core_api()
    try:
        resp = core_v1_api.read_namespaced_pod(name, namespace, **kwargs)
    except ApiException:
        LOG.exception('Read pod failed')
        raise
    else:
        return resp


def read_pod_status(name, namespace='default', **kwargs):   # pragma: no cover
    return read_pod(name).status.phase


def create_config_map(name,
                      data,
                      namespace='default',
                      wait=False,
                      **kwargs):   # pragma: no cover
    core_v1_api = get_core_api()
    metadata = client.V1ObjectMeta(name=name)
    body = client.V1ConfigMap(data=data, metadata=metadata)
    try:
        core_v1_api.create_namespaced_config_map(namespace, body, **kwargs)
    except ApiException:
        LOG.exception('Create config map failed')
        raise


def delete_config_map(name,
                      namespace='default',
                      wait=False,
                      **kwargs):     # pragma: no cover
    core_v1_api = get_core_api()
    body = kwargs.get('body', client.V1DeleteOptions())
    kwargs.pop('body', None)
    try:
        core_v1_api.delete_namespaced_config_map(name,
                                                 namespace,
                                                 body,
                                                 **kwargs)
    except ApiException:
        LOG.exception('Delete config map failed')
        raise


def get_pod_list(namespace='default'):      # pragma: no cover
    core_v1_api = get_core_api()
    try:
        return core_v1_api.list_namespaced_pod(namespace=namespace)
    except ApiException:
        LOG.exception('Get pod list failed')
        raise
