# -*- coding: utf-8 -*-
#
# uds/urls.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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

from django.conf.urls import url

from legal.uds.views import mainpage, htmllist, xmllist, csvlist, jsonlist


urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^list/$', htmllist, name='htmllist'),
    url(r'^xmllist/$', xmllist, name='xmllist'),
    url(r'^csvlist/$', csvlist, name='csvlist'),
    url(r'^jsonlist/$', jsonlist, name='jsonlist'),
]
