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

from functools import reduce

import jinja2
import logging

from yardstick.common.task_template import finalize_for_yaml
from yardstick.common.utils import try_int
from yardstick.common.yaml_loader import yaml_load

LOG = logging.getLogger(__name__)


def render(vnf_model, **kwargs):
    """Render jinja2 VNF template
    Do not check for missing arguments

    :param vnf_model: string that contains template
    :param kwargs: Dict with template arguments
    :returns:rendered template str
    """

    return jinja2.Template(vnf_model, finalize=finalize_for_yaml).render(**kwargs)


def generate_vnfd(vnf_model, node):
    """

    :param vnf_model: VNF definition template, e.g. tg_ping_tpl.yaml
    :param node: node configuration taken from pod.yaml
    :return: Complete VNF Descriptor that will be taken
             as input for GenericVNF.__init__
    """
    # get is unused as global method inside template
    # node["get"] = key_flatten_get
    node["get"] = deepgetitem
    # Set Node details to default if not defined in pod file
    # we CANNOT use TaskTemplate.render because it does not allow
    # for missing variables, we need to allow password for key_filename
    # to be undefined
    rendered_vnfd = render(vnf_model, **node)
    # This is done to get rid of issues with serializing node
    del node["get"]
    filled_vnfd = yaml_load(rendered_vnfd)
    return filled_vnfd


# dict_flatten was causing recursion errors with Jinja2 so we removed and replaced
# which this function from stackoverflow that doesn't require generating entire dictionaries
# each time we query a key
def deepgetitem(obj, item, default=None):
    """Steps through an item chain to get the ultimate value.

    If ultimate value or path to value does not exist, does not raise
    an exception and instead returns `fallback`.

    Based on
    https://stackoverflow.com/a/38623359
    https://stackoverflow.com/users/1820042/donny-winston

    add try_int to work with sequences

    >>> d = {'snl_final': {'about': {'_icsd': {'icsd_id': 1, 'fr': [2, 3], '0': 24, 0: 4}}}}
    >>> deepgetitem(d, 'snl_final.about._icsd.icsd_id')
    1
    >>> deepgetitem(d, 'snl_final.about._sandbox.sbx_id')
    >>>
    >>> deepgetitem(d, 'snl_final.about._icsd.fr.1')
    3
    >>> deepgetitem(d, 'snl_final.about._icsd.0')
    24
    """
    def getitem(obj, name):
        # try string then convert to int
        try:
            return obj[name]
        except (KeyError, TypeError, IndexError):
            name = try_int(name)
            try:
                return obj[name]
            except (KeyError, TypeError, IndexError):
                return default
    return reduce(getitem, item.split('.'), obj)
