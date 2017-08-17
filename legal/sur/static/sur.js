//
// sur/static/sur.js
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

    var submit;

    function submit_click(event) {
	submit = event.target.name;
    }

    function partyform_validate(event) {
	var p = $('#id_party');
	if ((submit != 'submit_back') &&
	    (p.val().trim().length < p.attr('data-minLen'))) {
	    alert('Řetězec musí obsahovat nejméně ' +
		  p.attr('data-minLenText') + '!');
	    return false;
	}
	return true;
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
	$('#id_partyform').submit(partyform_validate);
	$('input[type=submit]').click(submit_click);
    }
    if ($('#id_partybatchform').length) {
	$('#id_load_button').click(partybatchform_load_button_onclick);
	$('#id_load').change(partybatchform_load_onchange);
    }
});
