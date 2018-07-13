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
from yardstick.common import exceptions


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def get_core_api():     # pragma: no cover
    try:
        config.load_kube_config(config_file=consts.K8S_CONF_FILE)
    except IOError:
        raise exceptions.KubernetesConfigFileNotFound()
    return client.CoreV1Api()


def get_extensions_v1beta_api():
    try:
        config.load_kube_config(config_file=consts.K8S_CONF_FILE)
    except IOError:
        raise exceptions.KubernetesConfigFileNotFound()
    return client.ApiextensionsV1beta1Api()


def get_custom_objects_api():
    try:
        config.load_kube_config(config_file=consts.K8S_CONF_FILE)
    except IOError:
        raise exceptions.KubernetesConfigFileNotFound()
    return client.CustomObjectsApi()


def get_node_list(**kwargs):        # pragma: no cover
    core_v1_api = get_core_api()
    try:
        return core_v1_api.list_node(**kwargs)
    except ApiException:
        LOG.exception('Get node list failed')
        raise


def create_service(template,
                   namespace='default',
                   wait=False,
                   **kwargs):       # pragma: no cover
    # pylint: disable=unused-argument
    core_v1_api = get_core_api()
    metadata = client.V1ObjectMeta(**template.get('metadata', {}))

    ports = [client.V1ServicePort(**port) for port in
             template.get('spec', {}).get('ports', [])]
    template['spec']['ports'] = ports
    spec = client.V1ServiceSpec(**template.get('spec', {}))

    service = client.V1Service(metadata=metadata, spec=spec)

    try:
        core_v1_api.create_namespaced_service('default', service)
    except ApiException:
        LOG.exception('Create Service failed')
        raise


def delete_service(name,
                   namespace='default',
                   **kwargs):       # pragma: no cover
    core_v1_api = get_core_api()
    try:
        body = client.V1DeleteOptions()
        core_v1_api.delete_namespaced_service(name, namespace, body, **kwargs)
    except ApiException:
        LOG.exception('Delete Service failed')


def get_service_list(namespace='default', **kwargs):
    core_v1_api = get_core_api()
    try:
        return core_v1_api.list_namespaced_service(namespace, **kwargs)
    except ApiException:
        LOG.exception('Get Service list failed')
        raise


def get_service_by_name(name):      # pragma: no cover
    service_list = get_service_list()
    return next((s.spec for s in service_list.items if s.metadata.name == name), None)


def create_replication_controller(template,
                                  namespace='default',
                                  wait=False,
                                  **kwargs):    # pragma: no cover
    # pylint: disable=unused-argument
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
    # pylint: disable=unused-argument
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
    # pylint: disable=unused-argument
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
    # pylint: disable=unused-argument
    return read_pod(name).status.phase


def create_config_map(name,
                      data,
                      namespace='default',
                      wait=False,
                      **kwargs):   # pragma: no cover
    # pylint: disable=unused-argument
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
    # pylint: disable=unused-argument
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


def create_custom_resource_definition(body):
    api = get_extensions_v1beta_api()
    body_obj = client.V1beta1CustomResourceDefinition(
        spec=body['spec'], metadata=body['metadata'])
    try:
        api.create_custom_resource_definition(body_obj)
    except ValueError:
        # NOTE(ralonsoh): bug in kubernetes-client/python 6.0.0
        # https://github.com/kubernetes-client/python/issues/491
        pass
    except ApiException:
        raise exceptions.KubernetesApiException(
            action='create', resource='CustomResourceDefinition')


def delete_custom_resource_definition(name):
    api = get_extensions_v1beta_api()
    body_obj = client.V1DeleteOptions()
    try:
        api.delete_custom_resource_definition(name, body_obj)
    except ApiException:
        raise exceptions.KubernetesApiException(
            action='delete', resource='CustomResourceDefinition')


def get_custom_resource_definition(kind):
    api = get_extensions_v1beta_api()
    try:
        crd_list = api.list_custom_resource_definition()
        for crd_obj in (crd_obj for crd_obj in crd_list.items
                        if crd_obj.spec.names.kind == kind):
            return crd_obj
        return None
    except ApiException:
        raise exceptions.KubernetesApiException(
            action='delete', resource='CustomResourceDefinition')


def get_network(scope, group, version, plural, name, namespace='default'):
    api = get_custom_objects_api()
    try:
        if scope == consts.SCOPE_CLUSTER:
            network = api.get_cluster_custom_object(group, version, plural, name)
        else:
            network = api.get_namespaced_custom_object(
                group, version, namespace, plural, name)
    except ApiException:
        return
    return network


def create_network(scope, group, version, plural, body, name, namespace='default'):
    api = get_custom_objects_api()
    if get_network(scope, group, version, plural, name, namespace):
        logging.info('Network %s already exists' % name)
        return
    try:
        if scope == consts.SCOPE_CLUSTER:
            api.create_cluster_custom_object(group, version, plural, body)
        else:
            api.create_namespaced_custom_object(
                group, version, namespace, plural, body)
    except ApiException:
        raise exceptions.KubernetesApiException(
            action='create', resource='Custom Object: Network')


def delete_network(scope, group, version, plural, name, namespace='default'):
    api = get_custom_objects_api()
    try:
        if scope == consts.SCOPE_CLUSTER:
            api.delete_cluster_custom_object(group, version, plural, name, {})
        else:
            api.delete_namespaced_custom_object(
                group, version, namespace, plural, name, {})
    except ApiException:
        raise exceptions.KubernetesApiException(
            action='delete', resource='Custom Object: Network')


def get_pod_list(namespace='default'):      # pragma: no cover
    core_v1_api = get_core_api()
    try:
        return core_v1_api.list_namespaced_pod(namespace=namespace)
    except ApiException:
        LOG.exception('Get pod list failed')
        raise


def get_pod_by_name(name):  # pragma: no cover
    pod_list = get_pod_list()
    return next((n for n in pod_list.items if n.metadata.name.startswith(name)), None)


def get_volume_types():
    """Return the "volume" types supported by the current API"""
    return [vtype for vtype in client.V1Volume.attribute_map.values()
            if vtype != 'name']
