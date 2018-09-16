//-----------------------------------------------------------------------------
// nyacom (C) 2018.05 
// Note: JQuery is required
//-----------------------------------------------------------------------------
var $jq = $.noConflict(true);
$jq(function($){

	// on document ready
	$(document).ready(function(){
		get_status();
	});

	//$('#fpga_upload').on('click', function(){
	//	$.post('api/fpga', 'hoge=hoge');
	//});
	//
	
	// Reflesh button
	$('#btn_reflesh').on('click', function(){
		get_status();
	});

	// FPGA upload form control (for design purpose)
	$('#inp_fpga_upload').on('change', function(){
		$('#inp_fpga_upload_file').val($('#inp_fpga_upload').val());
	});

	// on FPGA reset button click
	$('#btn_fpga_reset').on('click', function() {
		if (confirm("Are you sure?")) {
			$.ajax({
				url         : '/api/fpga',
				type        : 'post',
				data        : JSON.stringify({ query : 'reset' }),
				cache       : false,
				contentType : 'application/json',
				dataType    : 'json'
			})
			.done(function(data, textStatus, jqXHR){
				//alert(form_data);
			})
			.fail(function(jqXHR, textStatus, errorThrown){
				//alert('fail');
			});
		}
	});

	// on startup button click
	$('#btn_fpga_startup').on('click', function() {
		if (confirm("Are you want to configure FPGA with default *.bit file?")) {
			$.ajax({
				url         : '/api/fpga',
				type        : 'post',
				data        : JSON.stringify({ query : 'startup' }),
				cache       : false,
				contentType : 'application/json',
				dataType    : 'json'
			})
			.done(function(form_data, textStatus, jqXHR){
				//alert(form_data);
			})
			.fail(function(jqXHR, textStatus, errorThrown){
				//alert('fail');
			});
		}
	});

	// on upload button click
	$('#btn_fpga_upload').on('click', function() {
		var file_data = $('#inp_fpga_upload').prop("files")[0];
		var form_data = new FormData();
		form_data.append('bitstream', file_data);

		var url = ''
		switch ($('input[name=fpga_cfg_mode]:checked').val()) {
			case 'PROG16':
				url = '/api/fpga_prog16';
				break;
			case 'PROG16_PR':
				url = '/api/fpga_prog16_pr';
				break;
			case 'PROG8':
				url = '/api/fpga_prog8';
				break;
			case 'PROG8_PR':
				url = '/api/fpga_prog8_pr';
				break;
		}

		$.ajax({
			url         : url,
			type        : 'post',
			data        : form_data,
			cache       : false,
			contentType : false,
			processData : false,
			dataType    : 'json'
		})
		.done(function(form_data, textStatus, jqXHR){
			$('#inp_fpga_upload_file').val('');
			alert(form_data);
		})
		.fail(function(jqXHR, textStatus, errorThrown){
			$('#inp_fpga_upload_file').val('');
			alert('fail');
		});
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

	// obtain board status
	function get_status() {
		$.ajax({
			url         : '/api/status',
			type        : 'get',
			cache       : false,
			dataType    : 'json',
			timeout     : 50000
		})
		.done(function(data, textStatus, jqXHR){
			//console.log('DEBUG: received');
			board_led_ctl(data);
		})
		.fail(function(jqXHR, textStatus, errorThrown){
			console.log('ajax error at get_status');
		});
	}

	// board led control
	function board_led_ctl(stat) {
		if (stat['pwr']) {
			$('#led_power').addClass('led_green_on');
		} else {
			$('#led_power').removeClass('led_green_on');
		}
		if (stat['done']) {
			$('#led_done').addClass('led_green_on');
		} else {
			$('#led_done').removeClass('led_green_on');
		}
		if (stat['linkup']) {
			$('#led_linkup').addClass('led_green_on');
		} else {
			$('#led_linkup').removeClass('led_green_on');
		}

		// 8SEG 0
		if (stat['led'] & 0x01) {
			$('#led_8seg0_a').css('background-color', '#c30')
		} else {
			$('#led_8seg0_a').css('background-color', '#330')
		}
		if (stat['led'] & 0x02) {
			$('#led_8seg0_b').css('background-color', '#c30')
		} else {
			$('#led_8seg0_b').css('background-color', '#330')
		}
		if (stat['led'] & 0x04) {
			$('#led_8seg0_c').css('background-color', '#c30')
		} else {
			$('#led_8seg0_c').css('background-color', '#330')
		}
		if (stat['led'] & 0x08) {
			$('#led_8seg0_d').css('background-color', '#c30')
		} else {
			$('#led_8seg0_d').css('background-color', '#330')
		}
		if (stat['led'] & 0x10) {
			$('#led_8seg0_e').css('background-color', '#c30')
		} else {
			$('#led_8seg0_e').css('background-color', '#330')
		}
		if (stat['led'] & 0x20) {
			$('#led_8seg0_f').css('background-color', '#c30')
		} else {
			$('#led_8seg0_f').css('background-color', '#330')
		}
		if (stat['led'] & 0x40) {
			$('#led_8seg0_g').css('background-color', '#c30')
		} else {
			$('#led_8seg0_g').css('background-color', '#330')
		}
		if (stat['led'] & 0x80) {
			$('#led_8seg0_h').css('background-color', '#c30')
		} else {
			$('#led_8seg0_h').css('background-color', '#330')
		}

		// 8SEG 0
		if (stat['led'] & 0x01) {
			$('#led_8seg1_a').css('background-color', '#c30')
		} else {
			$('#led_8seg1_a').css('background-color', '#330')
		}
		if (stat['led'] & 0x02) {
			$('#led_8seg1_b').css('background-color', '#c30')
		} else {
			$('#led_8seg1_b').css('background-color', '#330')
		}
		if (stat['led'] & 0x04) {
			$('#led_8seg1_c').css('background-color', '#c30')
		} else {
			$('#led_8seg1_c').css('background-color', '#330')
		}
		if (stat['led'] & 0x08) {
			$('#led_8seg1_d').css('background-color', '#c30')
		} else {
			$('#led_8seg1_d').css('background-color', '#330')
		}
		if (stat['led'] & 0x10) {
			$('#led_8seg1_e').css('background-color', '#c30')
		} else {
			$('#led_8seg1_e').css('background-color', '#330')
		}
		if (stat['led'] & 0x20) {
			$('#led_8seg1_f').css('background-color', '#c30')
		} else {
			$('#led_8seg1_f').css('background-color', '#330')
		}
		if (stat['led'] & 0x40) {
			$('#led_8seg1_g').css('background-color', '#c30')
		} else {
			$('#led_8seg1_g').css('background-color', '#330')
		}
		if (stat['led'] & 0x80) {
			$('#led_8seg1_h').css('background-color', '#c30')
		} else {
			$('#led_8seg1_h').css('background-color', '#330')
		}
	}

	// Every 10s
	tmr1 = setInterval(function(){
		get_status();
	}, 10000);
});

