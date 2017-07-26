'use strict';

$.fn.c = (
    function(v) {
	if (v === undefined) {
	    return this.prop('checked');
	} else {
	    this.prop('checked', v);
	    return this;
	}
    }
)

$.fn.s = (
    function(v) {
	if (v === undefined) {
	    return this.prop('selected');
	} else {
	    this.prop('selected', v);
	    return this;
	}
    }
)

$.fn.d = (
    function(v) {
	if (v === undefined) {
	    return this.prop('disabled');
	} else {
	    this.prop('disabled', v);
	    return this;
	}
    }
)

$.fn.dp = (
    function(v) {
	if (v === undefined) {
	    return this.prop('disabled');
	} else {
	    this.prop('disabled', v);
	    return v;
	}
    }
)

$.fn.r = (
    function() {
	this.each(function() {
	    var $t = $(this);
	    if ($t.is('select')) {
		$t.children().first().attr('selected', true);
	    } else if (!$t.is('[type=radio]')) {
		$t.val(null);
	    }
	} );
	return this;
    }
)

function today() {
    var t = new Date;
    return (t.getDate() + 100).toString().substr(1) +
	'.' +
	(t.getMonth() + 101).toString().substr(1) +
	'.' +
	t.getFullYear();
}

function set_today() {
    $(this).prev('input').val(today());
    return false;
}

function class_enable(elem) {
    $('*', elem)
	.addBack()
	.not('.immune, .immune *')
	.removeClass('disabled')
	.filter('input, textarea, select')
	.d(false);
}

function class_disable(elem) {
    $('*', elem)
	.addBack()
	.not('.immune, .immune *')
	.addClass('disabled')
	.removeClass('err')
	.filter('input, textarea, select')
	.d(true)
	.r();
}

function currsel_change() {
    var t = $(this);
    if ((t.val() == 'OTH') && !(t.d())) {
    	t.next().d(false);
    } else {
    	t.next().d(true).r().removeClass('err');
    }
    return true;
}

$(function() {
    $('.currsel').change(currsel_change).change();
    $('.today').click(set_today);
    $.datepicker.setDefaults($.datepicker.regional['cs']);
    $.datepicker.setDefaults({
	showOtherMonths: true,
	selectOtherMonths: true,
	prevText: 'předchozí',
	nextText: 'následující'
    });
    $('input[type=text][name*=date]').datepicker();
    $('select').each(function() {
	var select = $(this);
	var selectedValue = select.find('option[selected]').val();
	if (selectedValue) {
	    select.val(selectedValue);
	} else {
	    select.prop('selectedIndex', 0);
	}
    });
});
