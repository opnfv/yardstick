##############################################################################
# Copyright (c) 2017 Rajesh Kudaka <4k.rajesh@gmail.com>
# Copyright (c) 2018 Intel Corporation.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'report' """

import ast
import re
import uuid

import jinja2
from api.utils import influx
from oslo_utils import encodeutils
from oslo_utils import uuidutils
from yardstick.common import constants as consts
from yardstick.common.utils import cliargs


class JSTree(object):
    """Data structure to parse data for use with the JS library jsTree"""
    def __init__(self):
        self._created_nodes = ['#']
        self.jstree_data = []

    def _create_node(self, _id):
        """Helper method for format_for_jstree to create each node.

        Creates the node (and any required parents) and keeps track
        of the created nodes.

        :param _id: (string) id of the node to be created
        :return: None
        """
        components = _id.split(".")

        if len(components) == 1:
            text = components[0]
            parent_id = "#"
        else:
            text = components[-1]
            parent_id = ".".join(components[:-1])
            # make sure the parent has been created
            if not parent_id in self._created_nodes:
                self._create_node(parent_id)

        self.jstree_data.append({"id": _id, "text": text, "parent": parent_id})
        self._created_nodes.append(_id)

    def format_for_jstree(self, data):
        """Format the data into the required format for jsTree.

        The data format expected is a list of key-value pairs which represent
        the data and label for each metric e.g.:

            [{'data': [0, ], 'label': 'tg__0.DropPackets'},
             {'data': [548, ], 'label': 'tg__0.LatencyAvg.5'},]

        This data is converted into the format required for jsTree to group and
        display the metrics in a hierarchial fashion, including creating a
        number of parent nodes e.g.::

            [{"id": "tg__0", "text": "tg__0", "parent": "#"},
             {"id": "tg__0.DropPackets", "text": "DropPackets", "parent": "tg__0"},
             {"id": "tg__0.LatencyAvg", "text": "LatencyAvg", "parent": "tg__0"},
             {"id": "tg__0.LatencyAvg.5", "text": "5", "parent": "tg__0.LatencyAvg"},]

        :param data: (list) data to be converted
        :return: list
        """
        self._created_nodes = ['#']
        self.jstree_data = []

        for item in data:
            self._create_node(item["label"])

        return self.jstree_data


class Report(object):
    """Report commands.

    Set of commands to manage reports.
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
            raise KeyError("Test case not found.")

    def _get_tasks(self):
        task_cmd = "select * from \"%s\" where task_id= '%s'"
        task_query = task_cmd % (self.yaml_name, self.task_id)
        query_exec = influx.query(task_query)
        if query_exec:
            return query_exec
        else:
            raise KeyError("Task ID or Test case not found.")

    def _generate_common(self, args):
        """Actions that are common to both report formats.

        Create the necessary data structure for rendering
        the report templates.
        """
        self._validate(args.yaml_name[0], args.task_id[0])

        self.db_fieldkeys = self._get_fieldkeys()

        self.db_task = self._get_tasks()

        field_keys = []
        datasets = []
        table_vals = {}

        field_keys = [encodeutils.to_utf8(field['fieldKey'])
                      for field in self.db_fieldkeys]

        for key in field_keys:
            self.Timestamp = []
            values = []
            for task in self.db_task:
                task_time = encodeutils.to_utf8(task['time'])
                if not isinstance(task_time, str):
                    task_time = str(task_time, 'utf8')
                if not isinstance(key, str):
                    key = str(key, 'utf8')
                task_time = task_time[11:]
                head, _, tail = task_time.partition('.')
                task_time = head + "." + tail[:6]
                self.Timestamp.append(task_time)
                if task[key] is None:
                    values.append(None)
                elif isinstance(task[key], (int, float)):
                    values.append(task[key])
                else:
                    values.append(ast.literal_eval(task[key]))
            datasets.append({'label': key, 'data': values})
            table_vals['Timestamp'] = self.Timestamp
            table_vals[key] = values

        return datasets, table_vals

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def generate(self, args):
        """Start report generation."""
        datasets, table_vals = self._generate_common(args)

        template_dir = consts.YARDSTICK_ROOT_PATH + "yardstick/common"
        template_environment = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(template_dir))

        context = {
            "datasets": datasets,
            "Timestamps": self.Timestamp,
            "task_id": self.task_id,
            "table": table_vals,
        }

        template_html = template_environment.get_template("report.html.j2")

        with open(consts.DEFAULT_HTML_FILE, "w") as file_open:
            file_open.write(template_html.render(context))

        print("Report generated. View %s" % consts.DEFAULT_HTML_FILE)

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def generate_nsb(self, args):
        """Start NSB report generation."""
        datasets, table_vals = self._generate_common(args)
        jstree_data = JSTree().format_for_jstree(datasets)

        template_dir = consts.YARDSTICK_ROOT_PATH + "yardstick/common"
        template_environment = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(template_dir),
            lstrip_blocks=True)

        context = {
            "Timestamps": self.Timestamp,
            "task_id": self.task_id,
            "table": table_vals,
            "jstree_nodes": jstree_data,
        }

        template_html = template_environment.get_template("nsb_report.html.j2")

        with open(consts.DEFAULT_HTML_FILE, "w") as file_open:
            file_open.write(template_html.render(context))

        print("Report generated. View %s" % consts.DEFAULT_HTML_FILE)
