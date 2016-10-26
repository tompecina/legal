# -*- coding: utf-8 -*-
#
# szr/glob.py
#
# Copyright (C) 2011-16 Tomáš Pecina <tomas@pecina.cz>
#
# This file is part of legal.pecina.cz, a web-based toolbox for lawyers.
#
# This application is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This application is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.         
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

supreme_court = 'NSJIMBM'
supreme_court_name = 'Nejvyšší soud'

supreme_administrative_court = 'NSS'
supreme_administrative_court_name = 'Nejvyšší správní soud'

root_url = 'http://infosoud.justice.cz/'
get_proc = 'InfoSoud/public/search.do?org=%s&cisloSenatu=%d&druhVec=%s' \
           '&bcVec=%d&rocnik=%d&typSoudu=%s&autoFill=true&type=spzn'
