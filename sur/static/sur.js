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
    if ($('#id_partyform').length) {
	$('#id_partyform').submit(mainform_validate);
	$('input[type=submit]').click(submit_click);
    }
});
