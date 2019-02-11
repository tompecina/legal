# -*- coding: utf-8 -*-
#
# dir/urls.py
#
# Copyright (C) 2011-19 Tomáš Pecina <tomas@pecina.cz>
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
from legal.dir.views import (
    mainpage, debtorform, debtordel, debtordelall, debtorbatchform,
    debtorexport)


urlpatterns = (
    url(r'^$', mainpage, name='mainpage'),
    url(r'^debtorform/(\d+)/$', debtorform, name='debtorform'),
    url(r'^debtorform/$', debtorform, name='debtorform'),
    url(r'^debtordel/(\d+)/$', debtordel, name='debtordel'),
    url(r'^debtordeleted/$',
        genrender,
        kwargs={
            'template': 'dir_debtordeleted.xhtml',
            'page_title': 'Smazání dlužníka'},
        name='debtordeleted'),
    url(r'^debtordelall/$', debtordelall, name='debtordelall'),
    url(r'^debtorbatchform/$', debtorbatchform, name='debtorbatchform'),
    url(r'^debtorexport/$', debtorexport, name='debtorexport'),
)
