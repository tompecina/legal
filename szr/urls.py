# -*- coding: utf-8 -*-
#
# szr/urls.py
#
# Copyright (C) 2011-17 Tomáš Pecina <tomas@pecina.cz>
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
from common.views import genrender
from szr.views import (
    mainpage, procform, procdel, procdelall, procbatchform, procexport, courts)


urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^procform/(\d+)/$', procform, name='procform'),
    url(r'^procform/$', procform, name='procform'),
    url(r'^procdel/(\d+)/$', procdel, name='procdel'),
    url(r'^procdeleted/$',
        genrender,
        kwargs={
            'template': 'szr_procdeleted.html',
            'page_title': 'Smazání řízení'},
        name='procdeleted'),
    url(r'^procdelall/$', procdelall, name='procdelall'),
    url(r'^procbatchform/$', procbatchform, name='procbatchform'),
    url(r'^procexport/$', procexport, name='procexport'),
    url(r'^courts/$', courts, name='courts'),
]
