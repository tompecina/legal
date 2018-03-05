//
// hjp/static/hjp.js
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

// css_classes: curr trdt

$(function() {

    function submit_mainform() {
	$('#id_next').val(this);
	$('#id_mainform').submit();
	return false;
    }

    function mainform_updatefields() {
	$('.curr').text($(($('#id_currency_0').val() == 'OTH') ?
	    '#id_currency_1' : '#id_currency_0').val().toUpperCase()
	    .replace('CZK', 'Kč'));
    }

    function mainform_updatemodels() {
	if ($('#id_fixed_amount').dp(!$('[value=fixed]').c())) {
	    $('#id_fixed_amount').r();
	    class_disable($('#id_fa'));
	} else {
	    class_enable($('#id_fa'));
	}
	if ($('#id_pa_rate').dp($('#id_ydconv')
	    .dp(!$('[value=per_annum]').c()))) {
	    $('#id_pa_rate').r();
	    $('#id_ydconv').val('ACT/ACT');
	    class_disable($('#id_pa'));
	} else {
	    class_enable($('#id_pa'));
	}
	if ($('#id_pm_rate').dp($('#id_mdconv')
	    .dp(!$('[value=per_mensem]').c()))) {
	    $('#id_pm_rate').r();
	    $('#id_mdconv').val('ACT');
	    class_disable($('#id_pm'));
	} else {
	    class_enable($('#id_pm'));
	}
	if ($('#id_pd_rate').dp(!$('[value=per_diem]').c())) {
	    $('#id_pd_rate').r();
	    class_disable($('#id_pd'));
	} else {
	    class_enable($('#id_pd'));
	}
    }

    function mainpage_reset_onclick() {
	if ($('.trdt').length ||
	    $('#id_title').val() ||
	    $('#id_note').val() ||
	    $('#id_internal_note').val()) {
	    return confirm('Skutečně chcete smazat pohledávku?');
	} else {
	    return true;
	}
    }

    function mainpage_load_button_onclick() {
	if ($('#id_load').val()) {
	    if ($('.trdt').length ||
		$('#id_title').val() ||
		$('#id_note').val() ||
		$('#id_internal_note').val()) {
		return confirm('Skutečně chcete načíst jinou pohledávku?');
	    } else {
		return true;
	    }
	} else {
	    alert('Nejprve vyberte soubor pro načtení');
	    return false;
	}
    }

    function mainpage_load_onchange() {
	$('#id_load_button').click();
	return true;
    }

    function transform_updatefields() {
	if ($('[value=debit]').c()) {
	    class_enable($('#id_amt'));
	    class_disable($('#id_rep'));
	    return;
	}
	if ($('[value=credit]').c()) {
	    class_enable($('#id_amt'));
	    class_enable($('#id_rep'));
	    return;
	}
	if ($('[value=balance]').c()) {
	    class_disable($('#id_amt'));
	    class_disable($('#id_rep'));
	    return;
	}
    }

    if ($('#id_mainform').length) {
	$('#id_next').r();
	$('#id_reset').click(mainpage_reset_onclick);
	$('#id_load_button').click(mainpage_load_button_onclick);
	$('#id_load').change(mainpage_load_onchange);
	$('#id_currency_0').change(mainform_updatefields).change();
	$('#id_currency_1').keyup(mainform_updatefields);
	$('#id_mainform a').click(submit_mainform);
	$('[name=model]').change(mainform_updatemodels).first().change();
	$('#id_rounding').change(function () { $('#id_mainform').submit(); });
    }
    if ($('#id_transform').length) {
	$('[name=transaction_type]').change(transform_updatefields)
	    .first().change();
    }
});
