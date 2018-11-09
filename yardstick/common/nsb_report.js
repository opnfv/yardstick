/*******************************************************************************
 * Copyright (c) 2017 Rajesh Kudaka <4k.rajesh@gmail.com>
 * Copyright (c) 2018 Intel Corporation.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Apache License, Version 2.0
 * which accompanies this distribution, and is available at
 * http://www.apache.org/licenses/LICENSE-2.0
 ******************************************************************************/

var None = null;

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
    var tab, tr, td, tn, tbody, keys, key, curr_data, val;
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
            val = curr_data[j];
            td = document.createElement('td');
            tn = document.createTextNode(val === None ? '' : val);
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

function create_graph(cnvGraph, timestamps)
{
    return new Chart(cnvGraph, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [],
        },
        options: {
            elements: {
                line: {
                    borderWidth: 2,
                    fill: false,
                    tension: 0,
                },
            },
            scales: {
                xAxes: [{
                    type: 'category',
                }],
                yAxes: [{
                    type: 'linear',
                }],
            },
            tooltips: {
                mode: 'point',
                intersect: true,
            },
            hover: {
                mode: 'index',
                intersect: false,
                animationDuration: 0,
            },
            legend: {
                position: 'bottom',
                labels: {
                    usePointStyle: true,
                },
            },
            animation: {
                duration: 0,
            },
            responsive: true,
            responsiveAnimationDuration: 0,
            maintainAspectRatio: false,
        },
    });
}

function update_graph(objGraph, datasets)
{
    var colors = [
        '#FF0000',  // Red
        '#228B22',  // ForestGreen
        '#FF8C00',  // DarkOrange
        '#00008B',  // DarkBlue
        '#FF00FF',  // Fuchsia
        '#9ACD32',  // YellowGreen
        '#FFD700',  // Gold
        '#4169E1',  // RoyalBlue
        '#A0522D',  // Sienna
        '#20B2AA',  // LightSeaGreen
        '#8A2BE2',  // BlueViolet
    ];

    var points = [
        {s: 'circle',   r: 3},
        {s: 'rect',     r: 4},
        {s: 'triangle', r: 4},
        {s: 'star',     r: 4},
        {s: 'rectRot',  r: 5},
    ];

    datasets.forEach(function(d, i) {
        var color = colors[i % colors.length];
        var point = points[i % points.length];
        d.borderColor = color;
        d.backgroundColor = color;
        d.pointStyle = point.s;
        d.pointRadius = point.r;
        d.pointHoverRadius = point.r + 1;
    });
    objGraph.data.datasets = datasets;
    objGraph.update();
}
