# -*- coding: utf-8 -*-
#
# hsp/urls.py
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
from .views import mainpage, debitform, debitdel, creditform, creditdel, \
                   balanceform, balancedel, fxrateform, fxrateform, fxratedel

urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^debitform/(\d+)/$', debitform, name='debitform'),
    url(r'^debitform/$', debitform, name='debitform'),
    url(r'^debitdel/(\d+)/$', debitdel, name='debitdel'),
    url(r'^creditform/(\d+)/$', creditform, name='creditform'),
    url(r'^creditform/$', creditform, name='creditform'),
    url(r'^creditdel/(\d+)/$', creditdel, name='creditdel'),
    url(r'^balanceform/(\d+)/$', balanceform, name='balanceform'),
    url(r'^balanceform/$', balanceform, name='balanceform'),
    url(r'^balancedel/(\d+)/$', balancedel, name='balancedel'),
    url(r'^fxrateform/(\d+)/$', fxrateform, name='fxrateform'),
    url(r'^fxrateform/$', fxrateform, name='fxrateform'),
    url(r'^fxratedel/(\d+)/$', fxratedel, name='fxratedel'),
]
