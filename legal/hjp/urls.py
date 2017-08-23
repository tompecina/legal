# -*- coding: utf-8 -*-
#
# hjp/urls.py
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
from legal.hjp.views import mainpage, transform, transdel


urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^transform/(\d+)/$', transform, name='transform'),
    url(r'^transform/$', transform, name='transform'),
    url(r'^transdel/(\d+)/$', transdel, name='transdel'),
    url(r'^transdeleted/$',
        genrender,
        kwargs={
            'template': 'hjp_transdeleted.xhtml',
            'page_title': 'Smazání transakce'},
        name='transdeleted'),
]
