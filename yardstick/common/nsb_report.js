/*******************************************************************************
 * Copyright (c) 2017 Rajesh Kudaka <4k.rajesh@gmail.com>
 * Copyright (c) 2018 Intel Corporation.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Apache License, Version 2.0
 * which accompanies this distribution, and is available at
 * http://www.apache.org/licenses/LICENSE-2.0
 ******************************************************************************/

function create_tree(jstree_data)
{
    $('#data_selector').jstree({
        plugins: ['checkbox'],
        checkbox: {
            three_state: false,
            whole_node: true,
            tie_selection: false,
        },
        core: {
            themes: {
                icons: false,
                stripes: true,
            },
            data: jstree_data,
        },
    });
}

function create_table(table_data, timestamps)
{
    var tab, tr, td, tn, tbody, keys, key, curr_data;
    // create table
    tab = document.getElementsByTagName('table')[0];
    tbody = document.createElement('tbody');
    // create table headings using timestamps
    tr = document.createElement('tr');
    td = document.createElement('td');
    tn = document.createTextNode('Timestamps');
    td.appendChild(tn);
    tr.appendChild(td);
    for (var k = 0; k < timestamps.length; k++) {
        td = document.createElement('td');
        tn = document.createTextNode(timestamps[k]);
        td.appendChild(tn);
        tr.appendChild(td);
    }
    tbody.appendChild(tr);
    // for each metric
    keys = Object.keys(table_data);
    for (var i = 0; i < keys.length; i++) {
        key = keys[i];
        tr = document.createElement('tr');
        td = document.createElement('td');
        tn = document.createTextNode(key);
        td.appendChild(tn);
        tr.appendChild(td);
        // add each piece of data as its own column
        curr_data = table_data[key];
        for (var j = 0; j < curr_data.length; j++) {
            td = document.createElement('td');
            tn = document.createTextNode(curr_data[j]);
            td.appendChild(tn);
            tr.appendChild(td);
        }
        tbody.appendChild(tr);
    }
    tab.appendChild(tbody);
}

function deleteRows()
{
    // delete rows of the table
    var tab = document.getElementsByTagName('table')[0];
    for (var i = tab.rows.length - 1; i >= 0; i--) {
        tab.deleteRow(i);
    }
}

function render_graph(plot_data, timestamps)
{
    $('#graph').highcharts({
        title: {
            text: 'Yardstick Graphs',
            x: -20,
        },
        chart: {
            marginLeft: 400,
            zoomType: 'x',
            type: 'spline',
        },
        xAxis: {
            crosshair: {
                width: 1,
                color: 'black',
            },
            title: {
                text: 'Timestamp',
            },
            categories: timestamps,
        },
        yAxis: {
            crosshair: {
                width: 1,
                color: 'black',
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080',
            }],
        },
        plotOptions: {
            series: {
                showCheckbox: false,
                visible: true,
            },
        },
        tooltip: {
            valueSuffix: '',
        },
        legend: {
            enabled: true,
        },
        series: plot_data,
    });
}
