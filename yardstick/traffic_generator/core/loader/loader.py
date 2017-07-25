# Copyright 2015-2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Loader module definition.
"""

from yardstick.traffic_generator.conf import settings
from yardstick.traffic_generator.core.loader.loader_servant import LoaderServant
from yardstick.traffic_generator.tools.pkt_gen.trafficgen import ITrafficGenerator

class Loader(object):
    """Loader class - main object context holder.
    """
    _trafficgen_loader = None

    def __init__(self):
        """Loader ctor - initialization method.

        All data is read from configuration each time Loader instance is
        created. It is up to creator to maintain object life cycle if this
        behavior is unwanted.
        """
        self._trafficgen_loader = LoaderServant(
            settings.getValue('TRAFFICGEN_DIR'),
            settings.getValue('TRAFFICGEN'),
            ITrafficGenerator)

    def get_trafficgen(self):
        """Returns a new instance configured traffic generator.

        :return: ITrafficGenerator implementation if available, None otherwise.
        """
        return self._trafficgen_loader.get_class()()

    def get_trafficgen_class(self):
        """Returns type of currently configured traffic generator.

        :return: Type of ITrafficGenerator implementation if available.
            None otherwise.
        """
        return self._trafficgen_loader.get_class()

    def get_trafficgens(self):
        """Returns dictionary of all available traffic generators.

        :return: Dictionary of traffic generators.
            - key: name of the class which implements ITrafficGenerator,
            - value: Type of traffic generator which implements
              ITrafficGenerator.
        """
        return self._trafficgen_loader.get_classes()

    def get_trafficgens_printable(self):
        """Returns all available traffic generators in printable format.

        :return: String containing printable list of traffic generators.
        """
        return self._trafficgen_loader.get_classes_printable()
