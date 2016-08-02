# -*- coding: utf-8 -*-
#
# psj/urls.py
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

from django.conf.urls import url
from .views import mainpage, htmllist, xmllist, csvlist, courtinfo
from .cron import cron_courtrooms, cron_import, cron_schedule, cron_update

urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^list/$', htmllist, name='htmllist'),
    url(r'^xmllist/$', xmllist, name='xmllist'),
    url(r'^csvlist/$', csvlist, name='csvlist'),
    url(r'^court/(\w+)/$', courtinfo),
    url(r'^cron/courtrooms/$', cron_courtrooms),
    url(r'^cron/import/$', cron_import),
    url(r'^cron/schedule/$', cron_schedule),
    url(r'^cron/update/$', cron_update),
]
