function create_jstree(jstree_data, divIndex){
    $('#data_selector'+divIndex).jstree({
       plugins: ['checkbox'],
       checkbox: {
           three_state: false,
           whole_node: true,
           tie_selection: false,
       },
       'core' : {
           'themes' :{
               'icons': false,
               'stripes': true,
           },
           'data' : jstree_data
       },
   });
}  // end create_jstree

function create_table(table_data, timestamps, divIndex){
    var tab, th, tr, td, tn, row, col, thead, tbody;
    // create table
    tab = document.getElementById('table-pane'+ divIndex);
    thead=document.createElement('thead');
    tr = document.createElement('tr');
    tbody=document.createElement('tbody');
    th = document.createElement('th');
    //create table headings using timestamps
    for (col = 0; col < 1; col++){
        tr = document.createElement('tr');
        td = document.createElement('td');
        tn = document.createTextNode('Timestamps');
        td.appendChild(tn);
        tr.appendChild(td);
        for(row=0;row<timestamps.length;row++)
        {
            td = document.createElement('td');
            tn = document.createTextNode(timestamps[row]);
            td.appendChild(tn);
            tr.appendChild(td);
        }
    tbody.appendChild(tr);
    }
    console.log("arr keys: " + Object.keys(table_data))
    keys = Object.keys(table_data)
    // for each metric
    for (i=0; i< keys.length; i++){
        tr = document.createElement('tr');
        key = keys[i]
        console.log("curr_key: " + key)
        td = document.createElement('td');
        td.append(key)
        tr.append(td)
        curr_data = table_data[key]
        // add each piece of data as its own column
        for (j=0; j<curr_data.length; j++){
            td = document.createElement('td');
            td.append(curr_data[j])
            tr.append(td)
        }
        tbody.append(tr)
    }
    tab.appendChild(tbody);
} // end create_table

//delete rows of the table
function deleteRows(table_data, timestamps, divIndex){
    var tab = document.getElementById('table-pane'+ divIndex);
    var rowCount = $('#table-pane'+ divIndex).find('tr').length;
    console.log("row" + rowCount);
    $('#table-pane'+ divIndex).empty();
}

//TODO: Define create_table_old(table_data, timestamps)

function render_highcharts(plot_data, timestamps, divIndex){
    $('#graph'+divIndex).highcharts({
       title: {
         text: 'Yardstick Graphs',
         x: -20 //center
       },
       chart: {
              marginLeft: 400,
              zoomType: 'x',
              type: 'spline'
       },
       xAxis: {
         crosshair: {
             width: 1,
             color: 'black'
           },
           title: {
               text: 'Timestamp'
           },
           categories: timestamps
           },
       yAxis: {
           crosshair: {
               width: 1,
               color: 'black'
           },
           plotLines: [{
               value: 0,
               width: 1,
               color: '#808080'
           }]
       },
       plotOptions: {
           series: {
               showCheckbox: false,
               visible: true
           }
       },
       tooltip: {
           valueSuffix: ''
       },
       legend: {
           enabled: true,
       },
       series: plot_data,
    });
}  // end render_highcharts


