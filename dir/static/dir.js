$(function() {

    var submit;

    function submit_click(event) {
	submit = event.target.name;
    }

    function debtorbatchform_load_button_onclick() {
	if ($('#id_load').val()) {
	    return true;
	} else {
	    alert('Nejprve vyberte soubor pro načtení');
	    return false;
	}
    }

    function debtorbatchform_load_onchange() {
	$('#id_load_button').click();
	return true;
    }

    if ($('#id_debtorbatchform').length) {
	$('#id_load_button').click(debtorbatchform_load_button_onclick);
	$('#id_load').change(debtorbatchform_load_onchange);
    }
});
