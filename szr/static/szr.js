$(function() {
    var submit;
    function submit_click(event) {
	submit = event.target.name;
    }
    function procbatchform_load_button_onclick() {
	if ($('#id_load').val()) {
	    return true;
	} else {
	    alert('Nejprve vyberte soubor pro načtení');
	    return false;
	}
    }
    function procbatchform_load_onchange() {
	$('#id_load_button').click();
	return true;
    }
    if ($('#id_procbatchform').length) {
	$('#id_load_button').click(procbatchform_load_button_onclick);
	$('#id_load').change(procbatchform_load_onchange);
    }
});
