//
// knr/static/knr.js
//
// Copyright (C) 2011-17 Tomáš Pecina <tomas@pecina.cz>
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

$(function() {

    function mainpage_reset_onclick() {
	if (($('#id_items').val() != '0') ||
	    $('#id_title').val() ||
	    $('#id_calculation_note').val() ||
	    $('#id_internal_note').val()) {
	    return confirm('Skutečně chcete začít novou kalkulaci?');
	} else {
	    return true;
	}
    }

    function mainpage_load_button_onclick() {
	if ($('#id_load').val()) {
	    if (($('#id_items').val() != '0') ||
		$('#id_title').val() ||
		$('#id_calculation_note').val() ||
		$('#id_internal_note').val()) {
		return confirm('Skutečně chcete načíst jinou kalkulaci?');
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

    function placeform_search_onclick() {
	if ($('#id_addr').val() == '') {
	    alert('Do pole "Adresa" zadejte řetězec pro vyhledání');
	    return false;
	} else {
	    return true;
	}
    }

    function itemlist_apply_onclick() {
	return $('#id_new').val() != '';
    }

    function itemlist_new_onchange() {
	if ($('#id_new').val()) {
	    $('#id_apply').click();
	}
    }

    function itemform_off10_flag_onclick() {
	var o1 = $('#id_off10_flag');
	var o3 = $('#id_off30_flag');
	var o3l5 = $('#id_off30limit5000_flag');
	var o2l5 = $('#id_off20limit5000_flag');
	if (o1.c()) {
	    o3.c(false);
	    o3l5.c(false);
	    o2l5.c(false);
	}
	return true;
    }

    function itemform_off30_flag_onclick() {
	var o1 = $('#id_off10_flag');
	var o3 = $('#id_off30_flag');
	var o3l5 = $('#id_off30limit5000_flag');
	var o2l5 = $('#id_off20limit5000_flag');
	if (o3.c()) {
	    o1.c(false);
	    o3l5.c(false);
	    o2l5.c(false);
	}
	return true;
    }

    function itemform_off30limit5000_flag_onclick() {
	var o1 = $('#id_off10_flag');
	var o3 = $('#id_off30_flag');
	var o3l5 = $('#id_off30limit5000_flag');
	var o2l5 = $('#id_off20limit5000_flag');
	if (o3l5.c()) {
	    o1.c(false);
	    o3.c(false);
	    o2l5.c(false);
	}
	return true;
    }

    function itemform_off20limit5000_flag_onclick() {
	var o1 = $('#id_off10_flag');
	var o3 = $('#id_off30_flag');
	var o3l5 = $('#id_off30limit5000_flag');
	var o2l5 = $('#id_off20limit5000_flag');
	if (o2l5.c()) {
	    o1.c(false);
	    o3.c(false);
	    o3l5.c(false);
	}
	return true;
    }

    function itemform_halved_flag_onclick() {
	var h = $('#id_halved_flag');
	var ha = $('#id_halved_appeal_flag');
	if (h.c()) {
	    ha.c(false);
	}
	return true;
    }

    function itemform_halved_appeal_flag_onclick() {
	var h = $('#id_halved_flag');
	var ha = $('#id_halved_appeal_flag');
	if (ha.c()) {
	    h.c(false);
	}
	return true;
    }

    function itemform_multiple_flag_onclick() {
	var m = $('#id_multiple_flag');
	var m5 = $('#id_multiple50_flag');
	if (m.c()) {
	    m5.c(false);
	}
	return true;
    }

    function itemform_multiple50_flag_onclick() {
	var m = $('#id_multiple_flag');
	var m5 = $('#id_multiple50_flag');
	if (m5.c()) {
	    m.c(false);
	}
	return true;
    }

    function itemform_locset() {
	return ($('#id_from_lat').val() &&
		$('#id_from_lon').val() &&
		$('#id_to_lat').val() &&
		$('#id_to_lon').val());
    }

    function itemform_calcdist() {
	if (itemform_locset()) {
	    $('#id_calc').click();
	}
	return true;
    }

    function itemform_resetdist() {
	$('#id_trip_distance').r();
	$('#id_time_number').r();
	return true;
    }

    function itemform_from_sel_onchange() {
	if ($('#id_from_sel').val()) {
	    $('#id_from_apply').click();
	}
    }

    function itemform_from_apply_onclick() {
	if ($('#id_from_sel').val() != '') {
	    itemform_resetdist();
	    return true;
	} else {
	    return false;
	}
    }

    function itemform_from_search_onclick() {
	if ($('#id_from_address').val() == '') {
	    alert('Do pole "Adresa" zadejte řetězec pro vyhledání');
	    return false;
	} else {
	    return true;
	}
    }

    function itemform_to_sel_onchange() {
	if ($('#id_to_sel').val()) {
	    $('#id_to_apply').click();
	}
    }

    function itemform_to_apply_onclick() {
	if ($('#id_to_sel').val() != '') {
	    itemform_resetdist();
	    return true;
	} else {
	    return false;
	}
    }

    function itemform_to_search_onclick() {
	if ($('#id_to_address').val() == '') {
	    alert('Do pole "Adresa" zadejte řetězec pro vyhledání');
	    return false;
	} else
	    return true;
    }

    function itemform_calc_onclick() {
	if (!itemform_locset()) {
	    alert('Musí byt vyplněny zeměpisné souřadnice obou míst');
	    return false;
	} else {
	    return true;
	}
    }

    function itemform_car_sel_onchange() {
	if ($('#id_car_sel').val()) {
	    $('#id_car_apply').click();
	}
    }

    function itemform_car_apply_onclick() {
	return $('#id_car_sel').val() != '';
    }

    function itemform_formula_sel_onchange() {
	if ($('#id_formula_sel').val()) {
	    $('#id_formula_apply').click();
	}
    }

    function itemform_formula_apply_onclick() {
	return $('#id_formula_sel').val() != '';
    }

    switch ($('#id_type').val()) {
	case 'mainpage':
	    $('#id_reset').click(mainpage_reset_onclick);
	    $('#id_load_button').click(mainpage_load_button_onclick);
	    $('#id_load').change(mainpage_load_onchange);
	    break;
	case 'placeform':
	    $('#id_search').click(placeform_search_onclick);
	    break;
	case 'itemlist':
	    $('#id_apply').click(itemlist_apply_onclick);
	    $('#id_new').change(itemlist_new_onchange);
	    break;
	case 'service':
	    $('#id_off10_flag').click(itemform_off10_flag_onclick);
	    $('#id_off30_flag').click(itemform_off30_flag_onclick);
	    $('#id_off30limit5000_flag')
	        .click(itemform_off30limit5000_flag_onclick);
	    $('#id_off20limit5000_flag')
	        .click(itemform_off20limit5000_flag_onclick);
	    break;
	case 'flat':
	    $('#id_halved_flag').click(itemform_halved_flag_onclick);
	    $('#id_halved_appeal_flag')
	        .click(itemform_halved_appeal_flag_onclick);
	    $('#id_multiple_flag').click(itemform_multiple_flag_onclick);
	    $('#id_multiple50_flag').click(itemform_multiple50_flag_onclick);
	    break;
	case 'travel':
	    $('#id_from_sel').change(itemform_from_sel_onchange);
	    $('#id_from_apply').click(itemform_from_apply_onclick);
	    $('#id_from_search').click(itemform_from_search_onclick);
	    $('#id_from_lat').change(itemform_calcdist);
	    $('#id_from_lon').change(itemform_calcdist);
	    $('#id_to_sel').change(itemform_to_sel_onchange);
	    $('#id_to_apply').click(itemform_to_apply_onclick);
	    $('#id_to_search').click(itemform_to_search_onclick);
	    $('#id_to_lat').change(itemform_calcdist);
	    $('#id_to_lon').change(itemform_calcdist);
	    $('#id_calc').click(itemform_calc_onclick);
	    $('#id_car_sel').change(itemform_car_sel_onchange);
	    $('#id_car_apply').click(itemform_car_apply_onclick);
	    $('#id_formula_sel').change(itemform_formula_sel_onchange);
	    $('#id_formula_apply').click(itemform_formula_apply_onclick);
	    break;
    }
});
