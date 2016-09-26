$(function() {
    var submit;
    function submit_click(event) {
	submit = event.target.name;
    }
    function mainform_validate(event) {
	var p = $('#id_party');
	if ((submit != 'submit_back') &&
	    (p.val().trim().length < p.attr('data-minLen'))) {
	    alert('Řetězec musí obsahovat nejméně ' +
		  p.attr('data-minLenText') + '!');
	    return false;
	}
	return true;
    }
    function submit_partybatchform() {
	$('#id_next').val(this);
	$('#id_partybatchform').submit();
	return false;
    }
    function partybatchform_load_button_onclick() {
	if ($('#id_load').val()) {
	    return true;
	} else {
	    alert('Nejprve vyberte soubor pro načtení');
	    return false;
	}
    }
    function partybatchform_load_onchange() {
	$('#id_load_button').click();
	return true;
    }
    if ($('#id_partyform').length) {
	$('#id_partyform').submit(mainform_validate);
	$('input[type=submit]').click(submit_click);
    }
    if ($('#id_partybatchform').length) {
	$('#id_next').r();
	$('#id_load_button').click(partybatchform_load_button_onclick);
	$('#id_load').change(partybatchform_load_onchange);
    }
});
