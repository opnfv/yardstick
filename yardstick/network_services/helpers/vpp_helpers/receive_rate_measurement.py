# Copyright (c) 2019 Viosoft Corporation
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
#
# This is a modified copy of
# https://gerrit.fd.io/r/gitweb?p=csit.git;a=blob_plain;f=resources/libraries/python/MLRsearch/ReceiveRateMeasurement.py;hb=HEAD


class ReceiveRateMeasurement(object):
    """Structure defining the result of single Rr measurement."""

    def __init__(self, duration, target_tr, transmit_count, loss_count):
        """Constructor, normalize primary and compute secondary quantities.

        :param duration: Measurement duration [s].
        :param target_tr: Target transmit rate [pps].
            If bidirectional traffic is measured, this is bidirectional rate.
        :param transmit_count: Number of packets transmitted [1].
        :param loss_count: Number of packets transmitted but not received [1].
        :type duration: float
        :type target_tr: float
        :type transmit_count: int
        :type loss_count: int
        """
        self.duration = float(duration)
        self.target_tr = float(target_tr)
        self.transmit_count = int(transmit_count)
        self.loss_count = int(loss_count)
        self.receive_count = round(transmit_count - loss_count, 5)
        self.transmit_rate = round(transmit_count / self.duration, 5)
        self.loss_rate = round(loss_count / self.duration, 5)
        self.receive_rate = round(self.receive_count / self.duration, 5)
        self.loss_fraction = round(
            float(self.loss_count) / self.transmit_count, 5)
        # TODO: Do we want to store also the real time (duration + overhead)?

    def __str__(self):
        """Return string reporting input and loss fraction."""
        return "d={dur!s},Tr={rate!s},Df={frac!s}".format(
            dur=self.duration, rate=self.target_tr, frac=self.loss_fraction)

    def __repr__(self):
        """Return string evaluable as a constructor call."""
        return ("ReceiveRateMeasurement(duration={dur!r},target_tr={rate!r}"
                ",transmit_count={trans!r},loss_count={loss!r})".format(
            dur=self.duration, rate=self.target_tr,
            trans=self.transmit_count,
            loss=self.loss_count))
