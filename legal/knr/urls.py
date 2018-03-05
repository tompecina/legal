# -*- coding: utf-8 -*-
#
# knr/urls.py
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
from legal.knr.views import (
    mainpage, placeform, placelist, placedel, carform, carlist, cardel, formulaform, formulalist, formuladel, itemlist,
    itemform, itemdel, itemmove, presets)


urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^placeform/(\d+)/$', placeform, name='placeform'),
    url(r'^placeform/$', placeform, name='placeform'),
    url(r'^placelist/$', placelist, name='placelist'),
    url(r'^placedel/(\d+)/$', placedel, name='placedel'),
    url(r'^placedeleted/$',
        genrender,
        kwargs={
            'template': 'knr_placedeleted.xhtml',
            'page_title': 'Smazání místa'},
        name='placedeleted'),
    url(r'^carform/(\d+)/$', carform, name='carform'),
    url(r'^carform/$', carform, name='carform'),
    url(r'^carlist/$', carlist, name='carlist'),
    url(r'^cardel/(\d+)/$', cardel, name='cardel'),
    url(r'^cardeleted/$',
        genrender,
        kwargs={
            'template': 'knr_cardeleted.xhtml',
            'page_title': 'Smazání vozidla'},
        name='cardeleted'),
    url(r'^formulaform/(\d+)/$', formulaform, name='formulaform'),
    url(r'^formulaform/$', formulaform, name='formulaform'),
    url(r'^formulalist/$', formulalist, name='formulalist'),
    url(r'^formuladel/(\d+)/$', formuladel, name='formuladel'),
    url(r'^formuladeleted/$',
        genrender,
        kwargs={
            'template': 'knr_formuladeleted.xhtml',
            'page_title': 'Smazání předpisu'},
        name='formuladeleted'),
    url(r'^itemlist/$', itemlist, name='itemlist'),
    url(r'^itemform/(\d+)/$', itemform, name='itemform'),
    url(r'^itemform/$', itemform, name='itemform'),
    url(r'^itemdel/(\d+)/$', itemdel, name='itemdel'),
    url(r'^item(u)p/(\d+)/$', itemmove, name='itemup'),
    url(r'^item(d)own/(\d+)/$', itemmove, name='itemdown'),
    url(r'^itemdeleted/$',
        genrender,
        kwargs={
            'template': 'knr_itemdeleted.xhtml',
            'page_title': 'Smazání položky'},
        name='itemdeleted'),
    url(r'^presets/$', presets, name='presets'),
]
