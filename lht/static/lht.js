function initevents() {
    function updatefields() {
	if ($('[value=none]').c()) {
	    class_enable($('[value=none]').parents('.opt'));
	} else {
	    class_disable($('[value=none]').parents('.opt'));
	}
    }
    $('[value=none]').parent().addClass('immune');
    $('[name=preset]').change(updatefields).change();
}
