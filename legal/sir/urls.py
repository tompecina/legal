# -*- coding: utf-8 -*-
#
# sir/urls.py
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

from legal.common.views import genrender
from legal.sir.views import mainpage, insform, insdel, insdelall, insbatchform, insexport, courts


urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^insform/(\d+)/$', insform, name='insform'),
    url(r'^insform/$', insform, name='insform'),
    url(r'^insdel/(\d+)/$', insdel, name='insdel'),
    url(r'^insdeleted/$',
        genrender,
        kwargs={
            'template': 'sir_insdeleted.xhtml',
            'page_title': 'Smazání řízení'},
        name='insdeleted'),
    url(r'^insdelall/$', insdelall, name='insdelall'),
    url(r'^insbatchform/$', insbatchform, name='insbatchform'),
    url(r'^insexport/$', insexport, name='insexport'),
    url(r'^courts/$', courts, name='courts'),
]
