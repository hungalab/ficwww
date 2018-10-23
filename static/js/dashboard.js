//-----------------------------------------------------------------------------
// nyacom (C) 2018.05 
// Note: JQuery is required
//-----------------------------------------------------------------------------
var $jq = $.noConflict(true);
$jq(function($){
	//-------------------------------------------------------------------------
	// on document ready
	//-------------------------------------------------------------------------
	$(document).ready(function(){
		get_status();
	});

	//-------------------------------------------------------------------------
	// Reflesh button
	//-------------------------------------------------------------------------
	$('#btn_reflesh').on('click', function(){
		get_status();
	});

	//-------------------------------------------------------------------------
	// FPGA reset button click
	//-------------------------------------------------------------------------
	$('#btn_fpga_reset').on('click', function() {
		if (confirm("Are you sure?")) {
			$.ajax({
				url         : '/fpga',
				type        : 'delete',
				cache       : false,
				contentType : 'application/json',
				dataType    : 'json'
			})
			.done(function(data, textStatus, jqXHR){
				get_status();
				//alert(form_data);
			})
			.fail(function(jqXHR, textStatus, errorThrown){
				//alert('fail');
			});
		}
	});

	//-------------------------------------------------------------------------
	// on startup button click
	//-------------------------------------------------------------------------
	// FPGA upload form control (for design purpose)
	$('#inp_fpga_upload').on('change', function(){
		$('#inp_fpga_upload_file').val($('#inp_fpga_upload').val());
	});

	$('#btn_fpga_startup').on('click', function() {
		if (confirm("Are you want to configure FPGA with default *.bit file?")) {

			var json = JSON.stringify({
				mode : 'sm16',
				bitname : 'hoge.bin',
				bitstream : ''
			});

			$.ajax({
				url         : '/fpga',
				type        : 'post',
				data        : json,
				cache       : false,
				contentType : 'application/json',
				dataType    : 'json'
			})
			.done(function(form_data, textStatus, jqXHR) {
				//alert(form_data);
			})
			.fail(function(jqXHR, textStatus, errorThrown) {
				//alert('fail');
			});
		}
	});

	//-------------------------------------------------------------------------
	// upload button click
	//-------------------------------------------------------------------------
	$('#btn_fpga_upload').on('click', function() {
		file = $('#inp_fpga_upload').prop("files")[0];
		reader = new FileReader();
		reader.readAsDataURL(file);

		// When reader is transfering
		reader.onprogress = function(e) {
			$('#upload_status').text(e.loaded)
		}

		// When data transfer complete
		reader.onload = function(e) {
			base64_data = reader.result.split(',').pop();

			// Program mode
			var json = {
				"mode": $('input[name=fpga_cfg_mode]:checked').val(),
				"bitname": file.name,
				"bitstream": base64_data,
			}
			console.log(json);

			$.ajax({
				url         : '/fpga',
				type        : 'post',
				data        : JSON.stringify(json),
				cache       : false,
				contentType : 'application/json',
				dataType    : 'json',
				timeout     : 120000,
			})
			.done(function (form_data, textStatus, jqXHR) {
				//$('#inp_fpga_upload_file').val('');
				alert(form_data);
			})
			.fail(function (jqXHR, textStatus, errorThrown) {
				//$('#inp_fpga_upload_file').val('');
				alert('fail');
			});
		}
	});

	//----------------------------------------------------------------------------
	// Memory read/write
	//----------------------------------------------------------------------------
	
	// on btn_read_mem
	$('#btn_read_mem').on('click', function() {
		$.ajax({
			url         : '/api/reg',
			type        : 'post',
			data        : JSON.stringify({ query : 'read', addr : 0x00}),
			cache       : false,
			contentType : 'application/json',
			dataType    : 'json'
		})
		.done(function(form_data, textStatus, jqXHR){
			alert('done', form_data);
		})
		.fail(function(jqXHR, textStatus, errorThrown){
			//alert('fail');
		});
	});

	// on btn_write_mem
	$('#btn_write_mem').on('click', function() {
		alert('write_mem');
	});

	//----------------------------------------------------------------------------

	// obtain board status
	function get_status() {
		$.ajax({
			url         : '/status',
			type        : 'get',
			cache       : false,
			dataType    : 'json',
			timeout     : 50000
		})
		.done(function(data, textStatus, jqXHR){
			console.log('DEBUG: received');
			console.log(data);
			//board_led_ctl(data);

			var status = data['status'];

			// Power LED
			if (status['board']['power']) {
				$('#led_power').addClass('led_green_on');
			} else {
				$('#led_power').removeClass('led_green_on');
			}

			// Done LED
			if (status['fpga']['done']) {
				$('#led_done').addClass('led_green_on');
			} else {
				$('#led_done').removeClass('led_green_on');
			}

			// FPGA configuration
			$('#bit_file_name').text(status['fpga']['bitname']);	// bitfilename
			$('#config_time').text(status['fpga']['conftime']);		// configuration time
		})
		.fail(function(jqXHR, textStatus, errorThrown){
			console.log('ajax error at get_status');
		});
	}

	//// Every 10s
	//tmr1 = setInterval(function(){
	//	get_status();
	//}, 10000);
});

