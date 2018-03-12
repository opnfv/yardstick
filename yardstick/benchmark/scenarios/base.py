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

import abc

import six
from stevedore import extension

import yardstick.common.utils as utils


def _iter_scenario_classes(scenario_type=None):
    """Generator over all 'Scenario' subclasses

    This function will iterate over all 'Scenario' subclasses defined in this
    project and will load any class introduced by any installed plugin project,
    defined in 'entry_points' section, under 'yardstick.scenarios' subsection.
    """
    extension.ExtensionManager(namespace='yardstick.scenarios',
                               invoke_on_load=False)
    for scenario in utils.itersubclasses(Scenario):
        if not scenario_type:
            yield scenario
        elif getattr(scenario, '__scenario_type__', None) == scenario_type:
            yield scenario


@six.add_metaclass(abc.ABCMeta)
class Scenario(object):

    def setup(self):
        """Default setup implementation for Scenario classes"""
        pass

    @abc.abstractmethod
    def run(self, *args):
        """Entry point for scenario classes, called from runner worker"""

    def teardown(self):
        """Default teardown implementation for Scenario classes"""
        pass

    @staticmethod
    def get_types():
        """return a list of known runner type (class) names"""
        scenarios = []
        for scenario in _iter_scenario_classes():
            scenarios.append(scenario)
        return scenarios

    @staticmethod
    def get_cls(scenario_type):
        """return class of specified type"""
        for scenario in _iter_scenario_classes(scenario_type):
            return scenario

        raise RuntimeError("No such scenario type %s" % scenario_type)

    @staticmethod
    def get(scenario_type):
        """Returns instance of a scenario runner for execution type.
        """
        scenario = Scenario.get_cls(scenario_type)
        return scenario.__module__ + "." + scenario.__name__

    @classmethod
    def get_scenario_type(cls):
        """Return a string with the scenario type, if defined"""
        return str(getattr(cls, '__scenario_type__', None))

    @classmethod
    def get_description(cls):
        """Return a single line string with the class description

        This function will retrieve the class docstring and return the first
        line, or 'None' if it's empty.
        """
        return cls.__doc__.splitlines()[0] if cls.__doc__ else str(None)

    @staticmethod
    def _push_to_outputs(keys, values):
        """Return a dictionary given the keys and the values"""
        return dict(zip(keys, values))

    @staticmethod
    def _change_obj_to_dict(obj):
        """Return a dictionary from the __dict__ attribute of an object"""
        dic = {}
        for k, v in vars(obj).items():
            try:
                vars(v)
            except TypeError:
                dic[k] = v
        return dic
