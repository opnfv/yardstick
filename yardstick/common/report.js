function create_jstree(jstree_data){
    $('#data_selector').jstree({
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

function create_table(table_data, timestamps){
    var tab, tr, td, tn, row, col, tbody;
    // create table
    tab = document.getElementsByTagName('table')[0];
    tr = document.createElement('tr');
    tbody=document.createElement('tbody');
    //create table headings using timestamps
    td = document.createElement('td');
    tn = document.createTextNode('Timestamps');
    td.appendChild(tn);
    tr.appendChild(td);
    for(row=0; row<timestamps.length; row++)
    {
        td = document.createElement('td');
        tn = document.createTextNode(timestamps[row]);
        td.appendChild(tn);
        tr.appendChild(td);
    }
    tbody.appendChild(tr);
    console.log("arr keys: " + Object.keys(table_data))
    keys = Object.keys(table_data)
    // for each metric
    for (var i=0; i< keys.length; i++){
        tr = document.createElement('tr');
        key = keys[i]
        console.log("curr_key: " + key)
        td = document.createElement('td');
        td.append(key)
        tr.append(td)
        curr_data = table_data[key]
        // add each piece of data as its own column
        for (var j=0; j<curr_data.length; j++){
            td = document.createElement('td');
            td.append(curr_data[j])
            tr.append(td)
        }
        tbody.append(tr)
    }
    tab.appendChild(tbody);
} // end create_table

//delete rows of the table
function deleteRows(){
    var table = document.getElementsByTagName('table')[0];
    for (var i=((table.rows.length)-1); i>=0; i--){
        table.deleteRow(i);
    }
}

function render_highcharts(plot_data, timestamps){
    $('#graph').highcharts({
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
