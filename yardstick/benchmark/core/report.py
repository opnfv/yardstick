#############################################################################
# Copyright (c) 2017.
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

import influxdb
import os

from yardstick.common.utils import cliargs

from django.conf import settings
from django.template import Context
from django.template import Template

settings.configure()


class Report(object):
    """Report commands.

    Set of commands to manage benchmark tasks.
    """

    @cliargs("task_id", type=str, help=" task id", nargs=1)
    @cliargs("yaml_name", type=str, help=" Yaml file Name", nargs=1)
    def generate(self, args):
        """Start report generation."""
        # Influxdb Connection
        host = 'localhost'
        port = 8086
        user = 'root'
        password = 'root'
        dbname = 'yardstick'
        db = influxdb.InfluxDBClient(host, port, user, password, dbname)

        db.switch_database(dbname)

        # executing queries
        get_by_fieldkeys = 'SHOW FIELD KEYS FROM %s' % args.yaml_name[0]
        get_by_task = 'select * from %s where task_id= \'%s\'' % (
            args.yaml_name[0], args.task_id[0])
        db_fieldkeys = list(db.query(get_by_fieldkeys))
        db_task = list(db.query(get_by_task).get_points())

        field_keys = []
        temp_series = []
        table_vals = {}

        for field in db_fieldkeys[0]:
            field = field['fieldKey'].encode('utf-8')
            field_keys.append(field)

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
                    values.append(eval(task[key]))
            table_vals['Timestamp'] = Timestamp
            table_vals[key] = values
            series['name'] = key
            series['data'] = values
            temp_series.append(series)

        # generate template
        template = """
<html>
<body>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7\
/css/bootstrap.min.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1\
/jquery.min.js"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7\
/js/bootstrap.min.js"></script>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3\
/jquery.min.js"></script>
<script src="https://code.highcharts.com/highcharts.js"></script>
<script src="jquery.min.js"></script>
<script src="highcharts.js"></script>
</head>
<style>

table{
  overflow-y: scroll;
  height: 360px;
  display: block;
  }

 header,h3{
    font-family:Frutiger;
    clear: left;
    text-align: center;
}
</style>
<header class="jumbotron text-center">
  <h1>Yardstick User Interface</h1>
  <h4>Report of {{task_id}} Generated</h4>
</header>

<div class="container">
  <div class="row">
    <div class="col-md-4">
        <div class="table-responsive" >
        <table  class="table table-hover" > </table>
        </div>
    </div>
    <div class="col-md-8" >
    <div id="container" ></div>
   </div>
  </div>
</div>
<script>
  var arr, tab, th, tr, td, tn, row, col, thead, tbody;
  arr={{table|safe}}
  tab = document.getElementsByTagName('table')[0];
  thead=document.createElement('thead');
  tr = document.createElement('tr');
  for(row=0;row<Object.keys(arr).length;row++)
  {
      th = document.createElement('th');
      tn = document.createTextNode(Object.keys(arr).sort()[row]);
      th.appendChild(tn);
      tr.appendChild(th);
          thead.appendChild(tr);
  }
  tab.appendChild(thead);
  tbody=document.createElement('tbody');

  for (col = 0; col < arr[Object.keys(arr)[0]].length; col++){
  tr = document.createElement('tr');
  for(row=0;row<Object.keys(arr).length;row++)
  {
      td = document.createElement('td');
      tn = document.createTextNode(arr[Object.keys(arr).sort()[row]][col]);
      td.appendChild(tn);
      tr.appendChild(td);
  }
    tbody.appendChild(tr);
        }
tab.appendChild(tbody);

</script>

<script language="JavaScript">

$(function() {
  $('#container').highcharts({
    title: {
      text: 'Yardstick test results',
      x: -20 //center
    },
    subtitle: {
      text: 'Report of {{task_id}} Task Generated',
      x: -20
    },
    xAxis: {
      title: {
        text: 'Timestamp'
      },
      categories:{{Timestamp|safe}}
    },
    yAxis: {

      plotLines: [{
        value: 0,
        width: 1,
        color: '#808080'
      }]
    },
    tooltip: {
      valueSuffix: ''
    },
    legend: {
      layout: 'vertical',
      align: 'right',
      verticalAlign: 'middle',
      borderWidth: 0
    },
    series: {{series|safe}}
  });
});

</script>


</body>
</html>"""

        Template_html = Template(template)
        Context_html = Context({"series": temp_series,
                                "Timestamp": Timestamp,
                                "task_id": args.task_id[0],
                                "table": table_vals})

        file_open = open(os.path.join("/tmp/", "report.htm"), "w+")
        file_open.write(Template_html.render(Context_html))

        if not Timestamp:
            print ("Error : Report not generated")
        else:
            print ("Report generated.View /tmp/report.htm")
