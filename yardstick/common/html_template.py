#############################################################################
# Copyright (c) 2017 Rajesh Kudaka
#
# Author: Rajesh Kudaka 4k.rajesh@gmail.com
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#############################################################################
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
