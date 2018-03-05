//
// common/static/common.js
//
// Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
//
// This file is part of legal.pecina.cz, a web-based toolbox for lawyers.
//
// This application is free software: you can redistribute it and/or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This application is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//

'use strict';

// css_classes: immune disabled currsel today err

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

function go_back() {
    window.history.back();
}

function pager_close(event) {
    if ($('td.pager input').index(event.target) == -1) {
	$('td.pager span.num').css('display', 'none');
	$('td.pager a.num').css('display', 'inline');
	$('body').off('click');
    }
    return true;
}

function pager_click() {
    $('td.pager a.num').css('display', 'none');
    $('td.pager span.num').css('display', 'inline');
    $('body').click(pager_close);
    return false;
}

function pager_submit(event) {
    var form = $(this);
    var page = parseInt(form.find('input[name=page]')[0]['value']);
    var link = form.find('input[name=link]')[0]['value'];
    var batch = parseInt(form.find('input[name=batch]')[0]['value']);
    if (!isNaN(page) && page > 0) {
	$('body').off('click');
	window.location.replace(link + (--page * batch));
    }
    return false;
}

function help_show() {
    $('tr.help').css('display', 'table-row');
    $('a.help').text('skrýt').click(help_hide);
    return false;
}

function help_hide() {
    $('tr.help').css('display', 'none');
    $('a.help').text('nápověda').click(help_show);
    return false;
}

$(function() {
    $('.currsel').change(currsel_change).change();
    $('.today').click(set_today);
    $('a.back_link').click(go_back);
    $.datepicker.setDefaults($.datepicker.regional['cs']);
    $.datepicker.setDefaults({
	showOtherMonths: true,
	selectOtherMonths: true,
	prevText: 'předchozí',
	nextText: 'následující'
    });
    $('td.pager a.num').click(pager_click);
    $('td.pager form').submit(pager_submit);
    $('a.help').click(help_show);
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
