#############################################################################
# Copyright (c) 2017 Rajesh Kudaka
#
# Author: Rajesh Kudaka 4k.rajesh@gmail.com
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#############################################################################

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

report_template = """
<html>
    <head>
        <title>Yardstick Report</title>
        <link href="http://cdn.static.runoob.com/libs/bootstrap/3.3.7/css\
/bootstrap.min.css" rel="stylesheet">
    </head>
    <div class="content">
        <h3>Yardstick Report </h3>
        <hr/>
        <div>

            <div>Task ID : {{result.task_id}} </div>
            <div style="margin-top:5px;">Criteria :
                <font> {{result.criteria}}</font>
            </div>
            <hr/>

            <caption>Information</caption>
            <table class="table table-striped">
                <tr>
                    <th>#</th>
                    <th>key</th>
                    <th>value</th>
                </tr>
                <tbody>
                    {% for key, value in result.info.items() %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{key}}</td>
                        <td>{{value}}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <hr/>

            <caption>Test Cases</caption>
            <table class="table table-striped">
                <tr>
                    <th>#</th>
                    <th>key</th>
                    <th>value</th>
                </tr>
                <tbody>
                    {% for key, value in result.testcases.items() %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{key}}</td>
                        <td>{{value.criteria}}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

        </div>
    </div>
</html>
"""
