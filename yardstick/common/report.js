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

// may need to pass timestamps too...
function create_table(table_data){
    var tab, th, tr, td, tn, row, col, thead, tbody;
    // create table
    tab = document.getElementsByTagName('table')[0];
    thead=document.createElement('thead');
    tr = document.createElement('tr');
    tbody=document.createElement('tbody');

    //create table headings using timestamps
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
