##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Scenario base class
"""

import yardstick.common.utils as utils


class Scenario(object):

    def setup(self):
        ''' default impl for scenario setup '''
        pass

    def run(self, args):
        ''' catcher for not implemented run methods in subclasses '''
        raise RuntimeError("run method not implemented")

    def teardown(self):
        ''' default impl for scenario teardown '''
        pass

    @staticmethod
    def get(scenario_type):
        """Returns instance of a scenario runner for execution type.
        """
        for scenario in utils.itersubclasses(Scenario):
            if scenario_type == scenario.__scenario_type__:
                return scenario.__module__ + "." + scenario.__name__

        raise RuntimeError("No such scenario type %s" % scenario_type)
