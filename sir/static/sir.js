'use strict';

$(function() {

    var submit;

    function submit_click(event) {
	submit = event.target.name;
    }

    function insbatchform_load_button_onclick() {
	if ($('#id_load').val()) {
	    return true;
	} else {
	    alert('Nejprve vyberte soubor pro načtení');
	    return false;
	}
    }

    function insbatchform_load_onchange() {
	$('#id_load_button').click();
	return true;
    }

    if ($('#id_insbatchform').length) {
	$('#id_load_button').click(insbatchform_load_button_onclick);
	$('#id_load').change(insbatchform_load_onchange);
    }
});
