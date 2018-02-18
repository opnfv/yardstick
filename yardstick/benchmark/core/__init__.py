##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
"""
Yardstick benchmark core.
"""

from __future__ import print_function


class Param(object):
    """This class converts a parameter dictionary to an object."""

    def __init__(self, kwargs):
        # list
        self.inputfile = kwargs.get('inputfile')
        self.task_args = kwargs.get('task-args')
        self.task_args_file = kwargs.get('task-args-file')
        self.keep_deploy = kwargs.get('keep-deploy')
        self.parse_only = kwargs.get('parse-only')
        self.render_only = kwargs.get('render-only')
        self.output_file = kwargs.get('output-file', '/tmp/yardstick.out')
        self.suite = kwargs.get('suite')
        self.task_id = kwargs.get('task_id')
        self.yaml_name = kwargs.get('yaml_name')

        # list
        self.input_file = kwargs.get('input_file')

        # list
        self.casename = kwargs.get('casename')

        # list
        self.type = kwargs.get('type')
