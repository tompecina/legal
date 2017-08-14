# -*- coding: utf-8 -*-
#
# sur/urls.py
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

from legal.common.views import genrender
from legal.sur.views import mainpage, partyform, partydel, partydelall, partybatchform, partyexport


urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^partyform/(\d+)/$', partyform, name='partyform'),
    url(r'^partyform/$', partyform, name='partyform'),
    url(r'^partydel/(\d+)/$', partydel, name='partydel'),
    url(r'^partydeleted/$',
        genrender,
        kwargs={
            'template': 'sur_partydeleted.html',
            'page_title': 'Smazání účastníka'},
        name='partydeleted'),
    url(r'^partydelall/$', partydelall, name='partydelall'),
    url(r'^partybatchform/$', partybatchform, name='partybatchform'),
    url(r'^partyexport/$', partyexport, name='partyexport'),
]
