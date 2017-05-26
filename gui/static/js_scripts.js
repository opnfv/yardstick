$(document).ready(function() {
   // var url = 'http://10.223.197.182:5000/api/v1.0/vnf/';
    var url = 'http://' + document.domain + ':' + location.port + '/api/v1.0/tg/';
    var container = $(document.createElement('p'))
    $(document).ajaxStart(function(){
        $("#loader").removeClass('hidden').addClass('show');
    });

   $(document).ajaxComplete(function(){
        $("#loader").removeClass('show').addClass('hidden');
    });

    $.ajax({
        url: url,
        dataType: "json"
    }).then(function(data) {
        //var out = $.parseJson(data);
        var element = '';
        var res = data.result;
	$('#tg_types').append(element);
        $('#tg_types').removeClass('hidden').addClass('show');
	$('#result').removeClass('show').addClass('hidden');
        var tg_types = $('#tg_types').find(":button")
        tg_types.on('click', function(){
		var btnName=$(this).text();
		if(btnName==$(this).text()){
			$(this).button('loading').delay(1000).queue(function(){
        	    $(this).button('reset');
	            //$(this).removeClass('btn-primary').addClass('disabled');
        	    $(this).prop('disabled', true).css("pointer-events","none");
		    $(this).addClass("disabled");
	            $(this).dequeue();
        	});}

	            $.each(tg_types, function(){
                	$(this).attr('disabled', 'disabled')
    		   });
    	var vnf_type_url = url+$(this).attr('value')+'/vnf'
    $.ajax({
        url: vnf_type_url,
        dataType: "json"
    }).then(function(data) {
        //var out = $.parseJson(data);
        var element = '';
        var res = data.result;
	$.each(tg_types, function(){
		$(this).removeAttr("disabled");
    	});
    	var vnf_type_url = url+$(this).attr('value')+'/vnf'
	if (res == 0) {
		document.getElementById("dialog").click();
		document.getElementById("errMsg").innerHTML = "Invalid topology. IXIA is only supported with 2 server setup.. {(ixia) -> (VNF) -> (ixia)}. Please check sample configuration for reference /etc/yardstick/nodes/pod.yaml.ixia_example";
		return;
	}else if (res == 1) {
		document.getElementById("dialog").click();
		document.getElementById("errMsg").innerHTML = "Invalid topology. Software Traffic Generator is only supported with 3 server setup.. {(tg_1) -> (VNF) -> (tg_2)}. Please check sample configuration for reference /etc/yardstick/nodes/pod.yaml.example";
		return;
	}
        $.each(res,function(i, item){
        var button = '<p><button id="use-cases" class="btn btn-primary"  type="button" value='+item.toLowerCase()+'>'+item+'</button></p>'
        element = element + button

        console.log(item);

        });
        $('#vnf_types').append(element);
        $('#vnf_types').removeClass('hidden').addClass('show');
        $('#tg_types').removeClass('show').addClass('hidden');
	$('#result').removeClass('show').addClass('hidden');
        var vnf_types = $('#vnf_types').find(":button")
        vnf_types.on('click', function(){
		var btnName=$(this).text();
		if(btnName==$(this).text()){
			$(this).button('loading').delay(1000).queue(function(){
            $(this).button('reset');
            $(this).removeClass('btn-primary').addClass('disabled');
            $(this).prop('disabled', true).css("pointer-events","none");
			$(this).addClass("disabled");
            $(this).dequeue();
        });}
		    //alert($(this).attr('value'));
            //$(this).removeClass('btn-default').addClass('btn-success');
            $.each(vnf_types, function(){
                $(this).attr('disabled', 'disabled')
            });



    		url = 'http://' + document.domain + ':' + location.port + '/api/v1.0/vnf/';
		var deployment_type_url = url+$(this).attr('value')+'/deployment-types'
            $.ajax({
                url: deployment_type_url,
                dataType: "json"
            }).then(function(data) {

                var element = '';
                var res = data.result.deployment_types;
                $('.breadcrumb').append('<li><span class="divider"></span>'+data.result.vnf_type.toUpperCase()+'</li>');
                $.each(res,function(i, item){

                    var button = '<p><button id="deployment-types" class="btn btn-primary" type="button" value='+item.toLowerCase()+'>'+item+'</button></p>'
                    element = element + button

                    console.log(item);

                });
                $('#deployment_types').append(element);
				$('#vnf_types').removeClass('show').addClass('hidden');
                $('#deployment_types').removeClass('hidden').addClass('show');
                var deployment_types = $('#deployment_types').find(":button")
                deployment_types.on('click', function(){
				var btnName1=$(this).text();
				if(btnName1==$(this).text()){
					$(this).button('loading').delay(1000).queue(function(){
					$(this).button('reset');
					$(this).removeClass('btn-primary').addClass('disabled');
					$(this).prop('disabled', true).css("pointer-events","none");
					$(this).addClass("disabled");
					$(this).dequeue();
				});}


                    //alert($(this).attr('value'));
                   // $(this).removeClass('btn-default').addClass('btn-success');
                    $.each(deployment_types, function(){
                        $(this).attr('disabled', 'disabled')
                    });
            var test_type_url = url+data.result.vnf_type+'/'+$(this).attr('value')+'/test-types'
            $.ajax({
                url: test_type_url,
                dataType: "json"
            }).then(function(data) {
                var element = '';
                var res = data.result.test_type;
                $.each(res,function(i, item){

                    var button = '<p><button id="test-types" class="btn btn-primary" type="button" value='+item.toLowerCase()+'>'+item+'</button></p>'
                    element = element + button

                    console.log(item);

                });
                $('.breadcrumb').append('<li><span class="divider"></span>'+data.result.deployment_type.toUpperCase()+'</li>');
                $('#test_types').append(element);
				$('#deployment_types').removeClass('show').addClass('hidden');
                $('#test_types').removeClass('hidden').addClass('show');
                var test_types = $('#test_types').find(":button");
                test_types.on('click', function(){
				var test_type = $(this).attr('value');
				var btnName1=$(this).text();
				if(btnName1==$(this).text()){
					$(this).button('loading').delay(1000).queue(function(){
					$(this).button('reset');
					$(this).removeClass('btn-primary').addClass('disabled');
					$(this).prop('disabled', true).css("pointer-events","none");
					$(this).addClass("disabled");
					$(this).dequeue();
				});}


                    //alert($(this).attr('value'));
                   // $(this).removeClass('btn-default').addClass('btn-success');
                    $.each(test_types, function(){
                        $(this).attr('disabled', 'disabled')
                    });
                    $('.breadcrumb').append('<li><span class="divider"></span>'+$(this).attr('value').toUpperCase()+'</li>');
					if($(this).attr('value') == 'throughput' || $(this).attr('value') == 'latency' || $(this).attr('value') == 'latency_ixia' || $(this).attr('value') == 'throughput_ixia'){

					    $('#test_types').removeClass('show').addClass('hidden');
						$('#ip_version').removeClass('hidden').addClass('show');
						//$('html, body').animate({scrollTop:$(document).height()}, 'slow');
						var ip_versions = $('#ip_version').find(":button");
						//alert('hi');
						ip_versions.on('click', function(){
					var ip_version = $(this).attr('value');
                    $('.breadcrumb').append('<li><span class="divider"></span>'+ip_version.toUpperCase()+'</li>');
					url = url+data.result.vnf_type+'/'+data.result.deployment_type+'/'+test_type+'/'+ip_version

					//alert(url);
					var btnName1=$(this).text();
				    if(btnName1==$(this).text()){
					$(this).button('loading').delay(1000).queue(function(){
					$(this).button('reset');
					$(this).removeClass('btn-primary').addClass('disabled');
					$(this).prop('disabled', true).css("pointer-events","none");
					$(this).addClass("disabled");
					$(this).dequeue();
				});}
				    $.each(ip_versions, function(){
                       $(this).attr('disabled', 'disabled')
                    });
					$('#ip_version').removeClass('show').addClass('hidden');
					$('#packet_size').removeClass('hidden').addClass('show');
					//$('html, body').animate({scrollTop:$(document).height()}, 'slow');

					});
					var packet_sizes = $('#packet_size').find(":button")

					packet_sizes.on('click', function(){
					var packet_size = $(this).attr('value');
                    $('.breadcrumb').append('<li><span class="divider"></span>'+packet_size.toUpperCase()+'</li>');
					//alert(packet_size);
					var btnName1=$(this).text();
				    if(btnName1==$(this).text()){

						$(this).button('loading').delay(1000).queue(function(){
						$(this).button('reset');
						$(this).removeClass('btn-primary').addClass('disabled');
						$(this).prop('disabled', true).css("pointer-events","none");
						$(this).addClass("disabled");
						$(this).dequeue();
				});}
					$.each(packet_sizes, function(){
                        $(this).attr('disabled', 'disabled')
                    });

var test_case_url = url+'/'+packet_size+'/test-cases';
url = test_case_url
//var test_case_url = url
                    $.ajax({
                        url: test_case_url,
                        dataType: "json"
                    }).then(function(data) {
                        var element = '';
                        var res = data.result.details;
                        $.each(res,function(i, item){
                            //var button = '<p><button class="btn btn-primary" type="button" value='+i+'>'+item[1]+'</button></p>'
                            var button = '<div><div id="image-loader" class="pull-left hidden"><div class="loader show"></div></div><button  id="test-cases" class="pull-left btn btn-link ladda-button testcasesList" data-style="expand-left" type="button" value='+i+'  disabled="true"><span class="ladda-label">'+item+'</span></button></div><div class="clearfix"></div>'
                            element = element + button

                            console.log(i, item);


                        });

                    $('#test_cases').append(element);
						$('#test_cases').removeClass('hidden').addClass('show');
						$('#vnf_types').removeClass('show').addClass('hidden');
						$('#deployment_types').removeClass('show').addClass('hidden');
						$('#test_types').removeClass('show').addClass('hidden');
						$('#ip_version').removeClass('show').addClass('hidden');
						$('#packet_size').removeClass('show').addClass('hidden');
						$('#test_cases button').prop('disabled', false);
						$('html, body').animate({scrollTop:0}, 'slow');

                    var test_cases = $('#test_cases').find(":button")
                    test_cases.on('click', function(){
					window.open("/popup","Logging","menubar=no, status=no, scrollbars=no, width=800, height=1500");
					//window.open("/popup","Logging");
					 $(this).prev().removeClass('hidden');
                        //alert($(this).attr('value'));
                        $(this).removeClass('btn-primary').addClass('btn-link');
                        $(this).removeClass('btn-success').addClass('btn-link');
                        $(this).removeClass('btn-danger').addClass('btn-link');
                        $('#test_result_buttons').removeClass('show').addClass('hidden');
                        //$('#test_cases').prop('disabled', true);


					var rqst=$("#txt").val();
					var level=$("#level").val();
					var rate= $("#text").val();
						var dSelectedVal;
						var profile = $(".dropdown .btn").text();
						$(".dropdown-menu li label").each(function(){
							if($.trim(profile)==$.trim($(this).text())){
								dSelectedVal=$(this).prev().val();
							}
						});
						profile=profile.split(' ')[0]
                        //                        alert($(this).attr('value'));
						//var test_execute_url = url+data.result.vnf_type+'/'+data.result.test_type+'/test-cases/execute/'+$(this).attr('value');
						var test_execute_url = url+'/execute/'+$(this).attr('value');
                //        alert(test_execute_url);
						/*var dSelectedVal;
						var profile = $(".dropdown .btn").text();
						$(".dropdown-menu li label").each(function(){
							if($.trim(profile)==$.trim($(this).text())){
								dSelectedVal=$(this).prev().val();
							}
						});	*/
					//	profile=profile.split(' ')[0]


						setTimeout(function(){
                            $.each(test_cases, function(){
                            $(this).attr('disabled', 'disabled')
                        });

                        $.ajax({
                            url: test_execute_url,
                            dataType: "json"
                        }).then(function(data) {

                            var res = data.result;
		            var test_cases = $('#test_cases').find(":button");
                            var result_class ='btn-success white-c';

                            $.each(test_cases, function(){
                                $(this).removeAttr('disabled');
                                if ($(this).attr('value') == res.test_id) {
				    if (res.result == 0) {
                            		    var result_class ='btn-danger white-c';
	                                    $(this).removeClass('btn-warning').addClass(result_class);
				    } else {
                            		    var result_class ='btn-success white-c';
	                                    $(this).removeClass('btn-warning').addClass(result_class);
				    }

                                    //$(this).removeClass('btn-warning').addClass(result_class);
                                    if (res.vnf != "vepc" || res.tg_selected == "IXIA") {
					    $('#result').removeClass('hidden').addClass('show');
                                    }
							//$(this).addClass('result-text ladda-label');
									$(this).prev().addClass('hidden');
									$(this).on('click', function(){
										$(this).removeClass(result_class);
										$(this).removeClass('result-text ladda-label').addClass('btn-link');
									})
                                }

                            });
							         
                            console.log(res);
                        });},1);
                     });
                    });

					});

						}

					else{
						var ip_version = 'ipv4';
						var packet_size = '64b';


					 //url+data.result.vnf_type+'/'+data.result.deployment_type+'/'+test_type+'/'+ip_version



var test_case_url = url+data.result.vnf_type+'/'+data.result.deployment_type+'/'+test_type+'/'+ip_version+'/'+packet_size+'/test-cases';
//alert(test_case_url);
//var test_case_url = url
                    $.ajax({
                        url: test_case_url,
                        dataType: "json"
                    }).then(function(data) {
                        var element = '';
                        var res = data.result.details;
                        $.each(res,function(i, item){
                            //var button = '<p><button class="btn btn-primary" type="button" value='+i+'>'+item[1]+'</button></p>'
                            var button = '<div><div id="image-loader" class="pull-left hidden"><div class="loader show"></div></div><button  id="test-cases" class="pull-left btn btn-link ladda-button testcasesList" data-style="expand-left" type="button" value='+i+'  disabled="true"><span class="ladda-label">'+item+'</span></button></div><div class="clearfix"></div>'
                            element = element + button

                            console.log(i, item);


                        });

                    $('#test_cases').append(element);
						$('#test_cases').removeClass('hidden').addClass('show');
						$('#vnf_types').removeClass('show').addClass('hidden');
						$('#deployment_types').removeClass('show').addClass('hidden');
						$('#test_types').removeClass('show').addClass('hidden');
						$('#ip_version').removeClass('show').addClass('hidden');
						$('#packet_size').removeClass('show').addClass('hidden');
						$('#test_cases button').prop('disabled', false);

                    var test_cases = $('#test_cases').find(":button")
                    test_cases.on('click', function(){
					window.open("/popup","Logging","menubar=no, status=no, scrollbars=no, width=1000, height=800");
					//window.open("/popup","Logging");
					 $(this).prev().removeClass('hidden');
                        //alert($(this).attr('value'));
                        $(this).removeClass('btn-primary').addClass('btn-link');
                        $(this).removeClass('btn-success').addClass('btn-link');
                        $(this).removeClass('btn-danger').addClass('btn-link');
                        $('#test_result_buttons').removeClass('show').addClass('hidden');
                        //$('#test_cases').prop('disabled', true);


					var rqst=$("#txt").val();
					var level=$("#level").val();
					var rate= $("#text").val();
						var dSelectedVal;
						var profile = $(".dropdown .btn").text();
						$(".dropdown-menu li label").each(function(){
							if($.trim(profile)==$.trim($(this).text())){
								dSelectedVal=$(this).prev().val();
							}
						});
						profile=profile.split(' ')[0]
                        //                        alert($(this).attr('value'));
						var test_execute_url = url+data.result.vnf_type+'/'+data.result.deployment_type+'/'+data.result.test_type+'/ipv4/64b/test-cases/execute/'+$(this).attr('value');
						//var test_execute_url = url+'/execute/'+$(this).attr('value');
                       //alert(test_execute_url);
						/*var dSelectedVal;
						var profile = $(".dropdown .btn").text();
						$(".dropdown-menu li label").each(function(){
							if($.trim(profile)==$.trim($(this).text())){
								dSelectedVal=$(this).prev().val();
							}
						});	*/
					//	profile=profile.split(' ')[0]


						setTimeout(function(){
                            $.each(test_cases, function(){
                            $(this).attr('disabled', 'disabled')
                        });

                        $.ajax({
                            url: test_execute_url,
                            dataType: "json"
                        }).then(function(data) {

                            var res = data.result;
							var test_cases = $('#test_cases').find(":button");
                            var result_class ='btn-success white-c';

                            $.each(test_cases, function(){
                                $(this).removeAttr('disabled');
                                if ($(this).attr('value') == res.test_id) {
				    if (res.result == 0) {
                            		    var result_class ='btn-danger white-c';
	                                    $(this).removeClass('btn-warning').addClass(result_class);
				    } else {
                            		    var result_class ='btn-success white-c';
	                                    $(this).removeClass('btn-warning').addClass(result_class);
				    }
				    //if (res.test_type == "throughput") {
                                    if (res.vnf != "vepc" || res.tg_selected == "IXIA") {
				    	$('#result').removeClass('hidden').addClass('show');
				    }
							//		$(this).addClass('result-text ladda-label');
									$(this).prev().addClass('hidden');
									$(this).on('click', function(){
										$(this).removeClass(result_class);
										$(this).removeClass('result-text ladda-label').addClass('btn-link');
									})
                                }

                            });
							         
                            console.log(res);
                        });},1);
                     });
                    });



						}

					//var ip_versions = $('#ip_version').find(":button");
					//$('#packet_size').removeClass('hidden').addClass('show');
					//alert('hi');



					//alert(packet_size);


					//---------------------------------------------------------------------------------------------------------------------------------------------



					//---------------------------------------------------------------------------------------------------------------------------
                });

             });
           });
          });
        });
    });
    });
});
    $('button#result_statistics').on('click', function(){
        //alert('hi');
        var url = 'http://10.242.173.77:5000/api/v1.0/vnf/';
        var container = $(document.createElement('table'))

        $.ajax({
            url: url+'get-tg-statistics',
            dataType: "json"
        }).then(function(data) {
            //var out = $.parseJson(data);
            var element = '<table class="table table-bordered table-hover">';
            var res = data.result.tg_1;
            $.each(res,function(i, item){
                 var row = '<tr>'
                $.each(item, function(j, stat){
                    var col = '<td>'+stat+'</td>';
                    row = row + col;
                });
                row = row+'</tr>';
            //var button = '<p><button class="btn btn-primary" type="button" value='+item.toLowerCase()+'>'+item+'</button></p>'
                element = element + row;

			});
            element = element+'</table>' ;
            //console.log(element);
            $('#tg_1').append(element);
            //$('#tg_1').removeClass('hidden').addClass('show');


            var element = '<table class="table table-bordered table-hover">';
            var res = data.result.tg_2;
            $.each(res,function(i, item){

                 var row = '<tr>'

                $.each(item, function(j, stat){
                    var col = '<td>'+stat+'</td>';
                    row = row + col;
                });

                row = row+'</tr>';
            //var button = '<p><button class="btn btn-primary" type="button" value='+item.toLowerCase()+'>'+item+'</button></p>'
                element = element + row;

            });
            element = element+'</table>' ;
            //console.log(element);
            $('#tg_2').append(element);
            //$('#tg_2').removeClass('hidden').addClass('show');
        });
        $('#test_selection').removeClass('show').addClass('hidden');
        $('#result_statistics_data').removeClass('hidden').addClass('show');
    });
    $('button#result_summary').on('click', function(){
        //alert('hi');
        var url = 'http://10.242.173.77:5000/api/v1.0/vnf/';
        var container = $(document.createElement('table'))

        $.ajax({
            url: url+'get-test-summary',
            dataType: "json"
        }).then(function(data) {

        $('#tg_1_summary').append('<p>'+data.result.tg_1+'</p>');
        $('#tg_2_summary').append('<p>'+data.result.tg_2+'</p>');
        $('#tg_summary').append('<p>'+data.result.summary+'</p>');
        $('#test_selection').removeClass('show').addClass('hidden');
        $('#result_summary_data').removeClass('hidden').addClass('show');

        });
    });

    $('button#close_button').on('click', function(){
        //alert('close');
        $('#test_selection').removeClass('hidden').addClass('show');
        $('#result_statistics_data').removeClass('show').addClass('hidden');
        $('#tg_1').find('table').remove();
        $('#tg_2').find('table').remove();

     });
     $('button#close_button_summary').on('click', function(){
        //alert('close');
        $('#test_selection').removeClass('hidden').addClass('show');
        $('#result_summary_data').removeClass('show').addClass('hidden');
        $('#tg_1_summary p').text('');
        $('#tg_2_summary p').text('');
        $('#tg_summary p').text('');

     });

    $('#Modal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget) // Button that triggered the modal
        var img_src = 'static/img/'+button.data('test_name')+'.png' // Extract info from data-* attributes
  // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
  // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
        var modal = $(this)
        //alert(img_src)
       modal.find('.modal-body img').attr('src', img_src)
});
var clicked=false
$('#GraphModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget)

        // Button that triggered the modal
        // Extract info from data-* attributes
  // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
  // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
        //url_part = button.data('url');
        graph_url = url+'get-graph-data/';
        console.log(clicked);
        //clicked = true
        var modal = $(this)
        $.ajax({
            url: graph_url,
            dataType: "json"
            }).then(function(data) {
                graph_data = data.result
                //console.log(graph_data);


                    //clicked = true;
                google.charts.load('current', {'packages':['corechart']});
                google.charts.setOnLoadCallback(function(){
                var data = google.visualization.arrayToDataTable(graph_data.pps);

        var options = {
          title: 'Statistics for Packet Rate',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

        var chart = new google.visualization.LineChart(document.getElementById('graph_image_1'));

        chart.draw(data, options);

        var data = google.visualization.arrayToDataTable(graph_data.total);

        var options = {
          title: 'Statistics for Throughput',
          curveType: 'function',
          legend: { position: 'bottom' }
        };


        var chart = new google.visualization.LineChart(document.getElementById('graph_image_2'));

        chart.draw(data, options);
      });
                });

       //alert(img_src)
       //modal.find('#graph_image').attr('src', 'img/download.png')
	});
	$("#txt , #level").on("keydown", function(){
		var rqst = $('#txt').val();
		var level=$('#level').val();
		$('#test_cases').removeClass('hidden').addClass('show');
		if (((rqst == "" || rqst == null) || (level =="" || level == null)) || ((rqst == "" || rqst == null) && (level =="" || level == null))) {
			$('#test_cases button').addClass('disabled');
			$('.testcasesList').prop('disabled', true);
		}
		else{
			$('#test_cases button').removeClass('disabled');
			$('.testcasesList').prop('disabled', false);

		}

	});
	$("#txt , #level").on("keydown", function(){
		var rqst = $('#txt').val();
		var level=$('#level').val();
		$('#test_cases').removeClass('hidden').addClass('show');
		if (((rqst == "" || rqst == null) || (level =="" || level == null)) || ((rqst == "" || rqst == null) && (level =="" || level == null))) {
			$('#test_cases button').addClass('disabled');
			$('.testcasesList').prop('disabled', true);
		}
		else{
			$('#test_cases button').removeClass('disabled');
			$('.testcasesList').prop('disabled', false);

		}

	});
	$("#text ,.dropdown .btn ").on("keydown", function(){
		var rate = $('#text').val();
		var profile=$(".dropdown .btn").text()
		$('#test_cases').removeClass('hidden').addClass('show');
		if (((rate == "" || rate == null) || (profile == "Select Packet"))||((rate == "" || rate == null) && (profile == "Select Packet"))) {
			$('#test_cases button').addClass('disabled');
			$('.testcasesList').prop('disabled', true);
		}
		else{
			$('#test_cases button').removeClass('disabled');
			$('.testcasesList').prop('disabled', false);

		}

	});
	$( "#text" ).focusout(function() {
		if($(this).val()==""){
			$(".error").removeClass("hidden");
		}
		else{
			$(".error").addClass("hidden");
		}
    });
	$( "#level" ).focusout(function() {
		if($(this).val()==""){
			$(".error2").removeClass("hidden");
		}
		else{
			$(".error2").addClass("hidden");
		}
    });
	$( "#txt" ).focusout(function() {
		if($(this).val()==""){
			$(".error1").removeClass("hidden");
		}
		else{
			$(".error1").addClass("hidden");
		}
    });

	$(".dropdown-menu li").click(function(){
		var dSelectedVal=$(this).find('input').val();
		var dSelectedVal1=dSelectedVal.split('-')[1]
		var profile = $(".dropdown .btn").text();
		$('#test_cases').removeClass('hidden').addClass('show');
	});
});

