# Copyright (c) 2016-2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Generic file to map and build vnf discriptor """

from __future__ import absolute_import
import collections

import jinja2
import yaml


def render(vnf_model, **kwargs):
    """Render jinja2 VNF template

    :param vnf_model: string that contains template
    :param kwargs: Dict with template arguments
    :returns:rendered template str
    """

    return jinja2.Template(vnf_model).render(**kwargs)


def generate_vnfd(vnf_model, node):
    """

    :param vnf_model: VNF definition template, e.g. tg_ping_tpl.yaml
    :param node: node configuration taken from pod.yaml
    :return: Complete VNF Descriptor that will be taken
             as input for GenericVNF.__init__
    """
    # get is unused as global method inside template
    node["get"] = get
    # Set Node details to default if not defined in pod file
    # we CANNOT use TaskTemplate.render because it does not allow
    # for missing variables, we need to allow password for key_filename
    # to be undefined
    rendered_vnfd = render(vnf_model, **node)
    # This is done to get rid of issues with serializing node
    del node["get"]
    filled_vnfd = yaml.load(rendered_vnfd)
    return filled_vnfd


def dict_key_flatten(data):
    """ Convert nested dict structure to dotted key
        (e.g. {"a":{"b":1}} -> {"a.b":1}

    :param data: nested dictionary
    :return: flat dicrionary
    """
    next_data = {}

    # check for non-string iterables
    if not any((isinstance(v, collections.Iterable) and not isinstance(v, str))
               for v in data.values()):
        return data

    for key, val in data.items():
        if isinstance(val, collections.Mapping):
            for n_k, n_v in val.items():
                next_data["%s.%s" % (key, n_k)] = n_v
        elif isinstance(val, collections.Iterable) and not isinstance(val,
                                                                      str):
            for index, item in enumerate(val):
                next_data["%s%d" % (key, index)] = item
        else:
            next_data[key] = val

    return dict_key_flatten(next_data)


def get(obj, key, *args):
    """ Get template key from dictionary, get default value or raise an exception
    """
    data = dict_key_flatten(obj)
    return data.get(key, *args)
