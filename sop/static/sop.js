function initevents() {
    function updatefields() {
	if ($('#id_curr_0 [value=CZK]').s()) {
	    class_disable($('#id_fx_date_span'));
	    var t = new Date;
	    $('#id_fx_date')
		.val('01.' + (t.getMonth() + 101).toString().substr(1) +
		     '.' + t.getFullYear());
	} else {
	    class_enable($('#id_fx_date_span'));
	}			 
	return true;
    }
    $('#id_curr_0').change(updatefields).change();
}
