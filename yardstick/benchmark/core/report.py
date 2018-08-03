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

import ast
import os
import re
import uuid

import jinja2

from api.utils import influx
from oslo_utils import encodeutils
from oslo_utils import uuidutils
from yardstick.common import constants as consts
from yardstick.common.utils import cliargs


class Report(object):
    """Report commands.

    Set of commands to manage benchmark tasks.
    """

    def __init__(self):
        self.Timestamp = []
        self.yaml_name = ""
        self.task_id = ""

    def _validate(self, yaml_name, task_id):
        if re.match(r"^[\w-]+$", yaml_name):
            self.yaml_name = yaml_name
        else:
            raise ValueError("invalid yaml_name", yaml_name)

        if uuidutils.is_uuid_like(task_id):
            task_id = '{' + task_id + '}'
            task_uuid = (uuid.UUID(task_id))
            self.task_id = task_uuid
        else:
            raise ValueError("invalid task_id", task_id)

    def _get_fieldkeys(self):
        fieldkeys_cmd = "show field keys from \"%s\""
        fieldkeys_query = fieldkeys_cmd % (self.yaml_name)
        query_exec = influx.query(fieldkeys_query)
        if query_exec:
            return query_exec
        else:
            raise KeyError("Task ID or Test case not found..")

    def _get_tasks(self):
        task_cmd = "select * from \"%s\" where task_id= '%s'"
        task_query = task_cmd % (self.yaml_name, self.task_id)
        query_exec = influx.query(task_query)
        if query_exec:
            return query_exec
        else:
            raise KeyError("Task ID or Test case not found..")

    def _create_node(self, id):
        components = id.split(".")

        if len(components) == 1:
            text = components[0]
            parent_id = "#"
        else:
            text = components[-1]
            parent_id = ".".join(components[:-1])
            # make sure the parent has been created;
        if not parent_id in self.created_nodes and parent_id != "#":
            self._create_node(parent_id)

        self.jstree_data.append({"id": id, "text": text, "parent": parent_id})
        self.created_nodes.append(id)

    def format_for_jstree(self, data):
        self.jstree_data = []
        self.created_nodes = []

        for item in data:
            id = item["name"]
            self._create_node(id)

        return self.jstree_data

    def _generate_common(self, args):
        """Actions that are common to both report formats.

        Create the necessary data structure for rendering
        the report templates.
        """
        self._validate(args.yaml_name[0], args.task_id[0])

        self.db_fieldkeys = self._get_fieldkeys()

        self.db_task = self._get_tasks()

        field_keys = []
        temp_series = []
        table_vals = {}

        field_keys = [encodeutils.to_utf8(field['fieldKey'])
                      for field in self.db_fieldkeys]

        for key in field_keys:
            self.Timestamp = []
            series = {}
            values = []
            for task in self.db_task:
                task_time = encodeutils.to_utf8(task['time'])
                if not isinstance(task_time, str):
                    task_time = str(task_time, 'utf8')
                    key = str(key, 'utf8')
                task_time = task_time[11:]
                head, _, tail = task_time.partition('.')
                task_time = head + "." + tail[:6]
                self.Timestamp.append(task_time)
                if task[key] is None:
                    values.append('')
                elif isinstance(task[key], (int, float)) is True:
                    values.append(task[key])
                else:
                    values.append(ast.literal_eval(task[key]))
            table_vals['Timestamp'] = self.Timestamp
            table_vals[key] = values
            series['name'] = key
            series['data'] = values
            temp_series.append(series)

        return temp_series, table_vals

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def generate(self, args):
        """Start report generation."""
        series, table_vals = self._generate_common(args)

        dirpath = os.path.dirname(os.path.realpath(__file__))
        template_dir = dirpath + "/../../common"
        TEMPLATE_ENVIRONMENT = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=False)

        context = {"series": series,
                   "Timestamps": self.Timestamp,
                   "task_id": self.task_id,
                   "table": table_vals,
                   "template_dir": template_dir}

        template_html = TEMPLATE_ENVIRONMENT.get_template("template.html")

        with open(consts.DEFAULT_HTML_FILE, "w") as file_open:
            file_open.write(template_html.render(context))

        print("Report generated. View /tmp/yardstick.htm")

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def generate_nsb(self, args):
        """Start NSB report generation."""
        series, table_vals = self._generate_common(args)
        jstree_data = self.format_for_jstree(series)

        dirpath = os.path.dirname(os.path.realpath(__file__))
        template_dir = dirpath + "/../../common"
        TEMPLATE_ENVIRONMENT = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=False)

        context = {"series": series,
                   "Timestamps": self.Timestamp,
                   "task_id": self.task_id,
                   "table": table_vals,
                   "template_dir": template_dir,
                   "jstree_nodes": jstree_data
                  }

        template_html = TEMPLATE_ENVIRONMENT.get_template("nsb_template.html")

        with open(consts.DEFAULT_HTML_FILE, "w") as file_open:
            file_open.write(template_html.render(context))

        print("Report generated. View /tmp/yardstick.htm")
