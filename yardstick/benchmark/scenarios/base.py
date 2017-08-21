# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this is a modified copy of
# rally/rally/benchmark/scenarios/base.py

""" Scenario base class
"""

from __future__ import absolute_import
import yardstick.common.utils as utils


class Scenario(object):

    def setup(self):
        """ default impl for scenario setup """
        pass

    def run(self, args):
        """ catcher for not implemented run methods in subclasses """
        raise RuntimeError("run method not implemented")

    def teardown(self):
        """ default impl for scenario teardown """
        pass

    @staticmethod
    def get_types():
        """return a list of known runner type (class) names"""
        scenarios = []
        for scenario in utils.itersubclasses(Scenario):
            scenarios.append(scenario)
        return scenarios

    @staticmethod
    def get_cls(scenario_type):
        """return class of specified type"""
        for scenario in utils.itersubclasses(Scenario):
            if scenario_type == scenario.__scenario_type__:
                return scenario

        raise RuntimeError("No such scenario type %s" % scenario_type)

    @staticmethod
    def get(scenario_type):
        """Returns instance of a scenario runner for execution type.
        """
        for scenario in utils.itersubclasses(Scenario):
            if scenario_type == scenario.__scenario_type__:
                return scenario.__module__ + "." + scenario.__name__

        raise RuntimeError("No such scenario type %s" % scenario_type)

    def _push_to_outputs(self, keys, values):
        return dict(zip(keys, values))

    def _change_obj_to_dict(self, obj):
        dic = {}
        for k, v in vars(obj).items():
            try:
                vars(v)
            except TypeError:
                dic[k] = v
        return dic
