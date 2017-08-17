//
// sop/static/sop.js
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
});
