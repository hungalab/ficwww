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
			$('#upload_status').text("Transfer:" + e.loaded + " bytes");
		}

		// When data transfer complete
		reader.onload = function(e) {
			$('#upload_status').text("Converting base64...");
			base64_data = reader.result.split(',').pop();

			$('#upload_status').text("Burn FPGA...");
			$('#upload_spinner').css('visibility', 'visible');

			// Program mode
			var json = {
				"mode": $('input[name=fpga_cfg_mode]:checked').val(),
				"bitname": file.name,
				"bitstream": base64_data,
			}

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
				$('#upload_status').text("Done!");
				$('#upload_spinner').css('visibility', 'hidden');
				get_status();
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
	// Reg READ Button
	$('#btn_reg_read').on('click', function() {
		// Check input value
		var addr = parseInt($('#inp_reg_addr').val(), 16);
		var has_error = false;

		if (!isFinite(addr)) {
			$('#inp_reg_addr').addClass('inp_val_error');
			has_error = true;
		} else {
			$('#inp_reg_addr').removeClass('inp_val_error');
		}

		if (has_error) {
			return;
		}

		var json = {
			"address" : addr,
		};

		$.ajax({
			url         : '/regread',
			type        : 'post',
			cache       : false,
			contentType : 'application/json',
			dataType    : 'json',
			data        : JSON.stringify(json),
		})
		.done(function(form_data, textStatus, jqXHR){
			console.log(form_data);
			if (form_data['return'] == 'success') {
				$('#inp_reg_val').val(form_data['data'].toString(16));
			} else {
				alert(form_data['error']);
			}
		})
		.fail(function(jqXHR, textStatus, errorThrown){
			alert('AJAX failed');
		});
	});

	// Reg WRITE Button
	$('#btn_reg_write').on('click', function() {
		// Check input value
		var addr = parseInt($('#inp_reg_addr').val(), 16);
		var val = parseInt($('#inp_reg_val').val(), 16);
		var has_error = false;

		if (!isFinite(addr)) {
			$('#inp_reg_addr').addClass('inp_val_error');
			has_error = true;
		} else {
			$('#inp_reg_addr').removeClass('inp_val_error');
		}

		if (!isFinite(val) || val > 0xff) {
			$('#inp_reg_val').addClass('inp_val_error');
			has_error = true;
		} else {
			$('#inp_reg_val').removeClass('inp_val_error');
		}

		if (has_error) {
			return;
		}

		var json = {
			"address" : addr,
			"data" : val,
		};

		$.ajax({
			url         : '/regwrite',
			type        : 'post',
			cache       : false,
			contentType : 'application/json',
			dataType    : 'json',
			data        : JSON.stringify(json),
		})
		.done(function(form_data, textStatus, jqXHR){
			console.log(form_data);
			if (form_data['return'] == 'success') {
			} else {
				alert(form_data['error']);
			}
		})
		.fail(function(jqXHR, textStatus, errorThrown){
			alert('AJAX failed');
		});
	});

	//----------------------------------------------------------------------------
	// obtain board status
	//----------------------------------------------------------------------------
	function get_status() {
		$.ajax({
			url         : '/status',
			type        : 'get',
			cache       : false,
			dataType    : 'json',
			timeout     : 50000
		})
		.done(function(data, textStatus, jqXHR){
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

			// Aurora link
			if (status['board']['link']) {
				$('#led_linkup').addClass('led_green_on');
			} else {
				$('#led_linkup').removeClass('led_green_on');
			}

			// LED0
			if (status['board']['led'] & 0x1) {
				$('#led_0').addClass('led_red_on');
			} else {
				$('#led_0').removeClass('led_red_on');
			}

			// LED1
			if (status['board']['led'] & 0x2) {
				$('#led_1').addClass('led_red_on');
			} else {
				$('#led_1').removeClass('led_red_on');
			}

			// SW ports
			//$('#sw_ports').text(status['switch']['ports']);
			//$('#sw_slots').text(status['switch']['slots']);
			$('#sw_config').text(JSON.stringify(status['switch']));

		})
		.fail(function(jqXHR, textStatus, errorThrown){
			console.log('ajax error at get_status');
		});
	}

	//----------------------------------------------------------------------------
	// SW configurator
	//----------------------------------------------------------------------------
	$('#inp_sw_ports').on('change', function() {
		ready_swconf_dom();
	});

	$('#inp_sw_slots').on('change', function() {
		ready_swconf_dom();
	});

	function ready_swconf_dom() {
		var ports = parseInt($('#inp_sw_ports').val());
		var slots = parseInt($('#inp_sw_slots').val());
		var has_error = false;

		if (!isFinite(ports)) {
			//$('#inp_reg_addr').addClass('inp_val_error');
			has_error = true;
		} else {
			//$('#inp_reg_addr').removeClass('inp_val_error');
		}

		if (!isFinite(slots)) {
			//$('#inp_reg_val').addClass('inp_val_error');
			has_error = true;
		} else {
			//$('#inp_reg_val').removeClass('inp_val_error');
		}

		if (has_error) {
			console.log(ports, slots)
			return;
		}

		$('#sw_conf_dom').empty(); // Once empty..

		var p, s;
		for (p = 0; p < ports; p++) {
			console.log('ports' + p);
			$('#sw_conf_dom').append('Port:' + p.toString());
			$('#sw_conf_dom').append('<div>');
			for (s = 0; s < slots; s++) {
				console.log('slots' + s);
				$('#sw_conf_dom').append('Slot' + s.toString() + ': <input type="text"><br>');
			}
			$('#sw_conf_dom').append('</div>');
		}
	}

	//----------------------------------------------------------------------------
	//// Every 10s
	//----------------------------------------------------------------------------
	//tmr1 = setInterval(function(){
	//	get_status();
	//}, 10000);
});

