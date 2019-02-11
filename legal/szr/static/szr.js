//
// szr/static/szr.js
//
// Copyright (C) 2011-19 Tomáš Pecina <tomas@pecina.cz>
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
