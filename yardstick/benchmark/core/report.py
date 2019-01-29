##############################################################################
# Copyright (c) 2017 Rajesh Kudaka <4k.rajesh@gmail.com>
# Copyright (c) 2018-2019 Intel Corporation.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Handler for yardstick command 'report' """

import re
import six
import uuid

import jinja2
from api.utils import influx
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

        The data format expected is a list of metric names e.g.:

            ['tg__0.DropPackets', 'tg__0.LatencyAvg.5']

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

        for metric in data:
            self._create_node(metric)

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

    def _get_metrics(self):
        metrics_cmd = "select * from \"%s\" where task_id = '%s'"
        metrics_query = metrics_cmd % (self.yaml_name, self.task_id)
        query_exec = influx.query(metrics_query)
        if query_exec:
            return query_exec
        else:
            raise KeyError("Task ID or Test case not found.")

    def _get_trimmed_timestamp(self, metric_time, resolution=4):
        if not isinstance(metric_time, str):
            metric_time = metric_time.encode('utf8') # PY2: unicode to str
        metric_time = metric_time[11:]               # skip date, keep time
        head, _, tail = metric_time.partition('.')   # split HH:MM:SS & nsZ
        metric_time = head + '.' + tail[:resolution] # join HH:MM:SS & .us
        return metric_time

    def _get_timestamps(self, metrics, resolution=6):
        # Extract the timestamps from a list of metrics
        timestamps = []
        for metric in metrics:
            metric_time = self._get_trimmed_timestamp(
                metric['time'], resolution)
            timestamps.append(metric_time)               # HH:MM:SS.micros
        return timestamps

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def _generate_common(self, args):
        """Actions that are common to both report formats.

        Create the necessary data structure for rendering
        the report templates.
        """
        self._validate(args.yaml_name[0], args.task_id[0])

        db_fieldkeys = self._get_fieldkeys()
        # list of dicts of:
        # - PY2: unicode key and unicode value
        # - PY3: str key and str value

        db_metrics = self._get_metrics()
        # list of dicts of:
        # - PY2: unicode key and { None | unicode | float | long | int } value
        # - PY3: str key and { None | str | float | int } value

        # extract fieldKey entries, and convert them to str where needed
        field_keys = [key if isinstance(key, str)       # PY3: already str
                          else key.encode('utf8')       # PY2: unicode to str
                      for key in
                          [field['fieldKey']
                           for field in db_fieldkeys]]

        # extract timestamps
        self.Timestamp = self._get_timestamps(db_metrics)

        # prepare return values
        datasets = []
        table_vals = {'Timestamp': self.Timestamp}

        # extract and convert field values
        for key in field_keys:
            values = []
            for metric in db_metrics:
                val = metric.get(key, None)
                if val is None:
                    # keep explicit None or missing entry as is
                    pass
                elif isinstance(val, (int, float)):
                    # keep plain int or float as is
                    pass
                elif six.PY2 and isinstance(val,
                            long):  # pylint: disable=undefined-variable
                    # PY2: long value would be rendered with trailing L,
                    # which JS does not support, so convert it to float
                    val = float(val)
                elif isinstance(val, six.string_types):
                    s = val
                    if not isinstance(s, str):
                        s = s.encode('utf8')            # PY2: unicode to str
                    try:
                        # convert until failure
                        val = s
                        val = float(s)
                        val = int(s)
                        if six.PY2 and isinstance(val,
                                    long):  # pylint: disable=undefined-variable
                            val = float(val)            # PY2: long to float
                    except ValueError:
                        pass
                else:
                    raise ValueError("Cannot convert %r" % val)
                values.append(val)
            datasets.append({'label': key, 'data': values})
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
        _, report_data = self._generate_common(args)
        report_time = report_data.pop('Timestamp')
        report_keys = sorted(report_data, key=str.lower)
        report_tree = JSTree().format_for_jstree(report_keys)
        report_meta = {
            "testcase": self.yaml_name,
            "task_id": self.task_id,
        }

        template_dir = consts.YARDSTICK_ROOT_PATH + "yardstick/common"
        template_environment = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(template_dir),
            lstrip_blocks=True)

        context = {
            "report_meta": report_meta,
            "report_data": report_data,
            "report_time": report_time,
            "report_keys": report_keys,
            "report_tree": report_tree,
        }

        template_html = template_environment.get_template("nsb_report.html.j2")

        with open(consts.DEFAULT_HTML_FILE, "w") as file_open:
            file_open.write(template_html.render(context))

        print("Report generated. View %s" % consts.DEFAULT_HTML_FILE)
