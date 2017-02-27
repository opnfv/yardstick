#############################################################################
# Copyright (c) 2017 Rajesh Kudaka
#
# Author: Rajesh Kudaka 4k.rajesh@gmail.com
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'report' """

from __future__ import print_function

from __future__ import absolute_import

import ast
import os
import re
import uuid

from api.utils import influx

from django.conf import settings
from django.template import Context
from django.template import Template

from oslo_utils import uuidutils
from yardstick.common.html_template import template
from yardstick.common.utils import cliargs

settings.configure()


class Report(object):
    """Report commands.

    Set of commands to manage benchmark tasks.
    """

    def _validate(self, yaml_name, task_id):
        if re.match("^[a-z0-9_-]+$", yaml_name):
            self.yaml_name = yaml_name
        else:
            raise ValueError("invalid yaml_name", yaml_name)

        if uuidutils.is_uuid_like(task_id):
            task_id = '{' + task_id + '}'
            task_uuid = (uuid.UUID(task_id))
            self.task_id = task_uuid
        else:
            raise ValueError("invalid task_id", task_id)

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def generate(self, args):
        """Start report generation."""
        self._validate(args.yaml_name[0], args.task_id[0])
        # executing queries
        fieldkeys_cmd = "show field keys from \"%s\""
        task_cmd = "select * from \"%s\" where task_id= '%s'"

        fieldkeys_query = fieldkeys_cmd % (self.yaml_name)
        task_query = task_cmd % (self.yaml_name, self.task_id)

        db_fieldkeys = influx.query(fieldkeys_query)
        db_task = influx.query(task_query)

        if not db_task or not db_fieldkeys:
            raise Exception("Task ID or Test case not found..")

        field_keys = []
        temp_series = []
        table_vals = {}

        field_keys = [field['fieldKey'].encode('utf-8')
                      for field in db_fieldkeys]

        for key in field_keys:
            Timestamp = []
            series = {}
            values = []
            for task in db_task:
                task_time = task['time'].encode('utf-8')
                task_time = task_time[11:]
                head, sep, tail = task_time.partition('.')
                task_time = head + "." + tail[:6]
                Timestamp.append(task_time)
                if isinstance(task[key], float) is True:
                    values.append(task[key])
                else:
                    values.append(ast.literal_eval(task[key]))
            table_vals['Timestamp'] = Timestamp
            table_vals[key] = values
            series['name'] = key
            series['data'] = values
            temp_series.append(series)

        Template_html = Template(template)
        Context_html = Context({"series": temp_series,
                                "Timestamp": Timestamp,
                                "task_id": self.task_id,
                                "table": table_vals})
        with open(os.path.join("/tmp/", "report.htm"), "w+") as file_open:
            file_open.write(Template_html.render(Context_html))

        print("Report generated. View /tmp/report.htm")
