/*******************************************************************************
 * Copyright (c) 2017 Rajesh Kudaka <4k.rajesh@gmail.com>
 * Copyright (c) 2018-2019 Intel Corporation.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Apache License, Version 2.0
 * which accompanies this distribution, and is available at
 * http://www.apache.org/licenses/LICENSE-2.0
 ******************************************************************************/

var None = null;

function create_tree(divTree, jstree_data)
{
    divTree.jstree({
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

function create_table(tblMetrics, table_data, timestamps, table_keys)
{
    var tbody = $('<tbody></tbody>');
    var tr0 = $('<tr></tr>');
    var th0 = $('<th></th>');
    var td0 = $('<td></td>');
    var tr;

    // create table headings using timestamps
    tr = tr0.clone().append(th0.clone().text('Timestamp'));
    timestamps.forEach(function(t) {
        tr.append(th0.clone().text(t));
    });
    tbody.append(tr);

    // for each metric
    table_keys.forEach(function(key) {
        tr = tr0.clone().append(td0.clone().text(key));
        // add each piece of data as its own column
        table_data[key].forEach(function(val) {
            tr.append(td0.clone().text(val === None ? '' : val));
        });
        tbody.append(tr);
    });

    // re-create table
    tblMetrics.empty().append(tbody);
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
                    showline: true,
                    spanGaps: true,
                },
            },
            scales: {
                xAxes: [{
                    type: 'category',
                    display: true,
                    labels: timestamps,
                    autoSkip: true,
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

function handle_tree(divTree, tblMetrics, objGraph, graph_data, table_data, timestamps)
{
    divTree.on('check_node.jstree uncheck_node.jstree', function(e, data) {
        var selected_keys = [];
        var selected_datasets = [];
        data.selected.forEach(function(sel) {
            var node = data.instance.get_node(sel);
            if (node.children.length == 0) {
                selected_keys.push(node.id);
                selected_datasets.push({
                    label: node.id,
                    data: graph_data[node.id],
                });
            }
        });
        create_table(tblMetrics, table_data, timestamps, selected_keys);
        update_graph(objGraph, selected_datasets);
    });
}
