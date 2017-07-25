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
"""rfc3511 Traffic Controller implementation.
"""
from yardstick.traffic_generator.core.traffic_controller import TrafficController
from yardstick.traffic_generator.core.results.results import IResults
from yardstick.traffic_generator.conf import settings


class TrafficControllerRFC3511(TrafficController, IResults):
    """Traffic controller for rfc3511 traffic

    Used to setup and control a traffic generator for an rfc3511 deployment
    traffic scenario.
    """

    def __init__(self, traffic_gen_class):
        """Initialise the trafficgen and store.

        :param traffic_gen_class: The traffic generator class to be used.
        """
        super(TrafficControllerRFC3511, self).__init__(traffic_gen_class)
        self._type = 'rfc3511'
        self._tests = int(settings.getValue('TRAFFICGEN_RFC3511_TESTS'))

    def send_traffic(self, traffic):
        """See TrafficController for description
        """
        if not self.traffic_required():
            return
        self._logger.debug('send_traffic with ' +
                           str(self._traffic_gen_class))

        # update type with detailed traffic value
        self._type = traffic['traffic_type']

        for packet_size in self._packet_sizes:
            # Merge framesize with the default traffic definition
            if 'l2' in traffic:
                traffic['l2'] = dict(traffic['l2'],
                                     **{'framesize': packet_size})
            else:
                traffic['l2'] = {'framesize': packet_size}

            self._traffic_gen_class._logger = self._logger
            if traffic['traffic_type'] == 'rfc3511_back2back':
                result = self._traffic_gen_class.send_rfc3511_back2back(
                    traffic, tests=self._tests, duration=self._duration, lossrate=self._lossrate)
            elif traffic['traffic_type'] == 'rfc3511_continuous':
                result = self._traffic_gen_class.send_cont_traffic(
                    traffic, duration=self._duration)
            elif traffic['traffic_type'] == 'rfc3511_quicktest':
                result = self._traffic_gen_class.send_rfc3511_throughput(
                    traffic, tests=self._tests, duration=self._duration, lossrate=self._lossrate)
            else:
                raise RuntimeError("Unsupported traffic type {} was "
                                   "detected".format(traffic['traffic_type']))

            result = self._append_results(result, packet_size)
            self._results.append(result)

    def send_traffic_async(self, traffic, function):
        """See TrafficController for description
        """
        if not self.traffic_required():
            return
        self._logger.debug('send_traffic_async with ' +
                           str(self._traffic_gen_class))

        # update type with detailed traffic value
        self._type = traffic['traffic_type']

        for packet_size in self._packet_sizes:
            traffic['l2'] = {'framesize': packet_size}
            self._traffic_gen_class.start_rfc3511_throughput(
                traffic,
                tests=self._tests,
                duration=self._duration)
            self._traffic_started = True
            if len(function['args']) > 0:
                function['function'](function['args'])
            else:
                function['function']()
            result = self._traffic_gen_class.wait_rfc3511_throughput()
            result = self._append_results(result, packet_size)
            self._results.append(result)
