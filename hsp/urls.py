# -*- coding: utf-8 -*-
#
# hsp/urls.py
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
from .views import (
    mainpage, debitform, debitdel, creditform, creditdel, balanceform,
    balancedel, fxrateform, fxratedel)

urlpatterns = [
    url(r'^$', mainpage, name='mainpage'),
    url(r'^debitform/(\d+)/$', debitform, name='debitform'),
    url(r'^debitform/$', debitform, name='debitform'),
    url(r'^debitdel/(\d+)/$', debitdel, name='debitdel'),
    url(r'^debitdeleted/$',
        genrender,
        kwargs={
            'template': 'hsp_debitdeleted.html',
            'page_title': 'Smazání závazku'},
        name='debitdeleted'),
    url(r'^creditform/(\d+)/$', creditform, name='creditform'),
    url(r'^creditform/$', creditform, name='creditform'),
    url(r'^creditdel/(\d+)/$', creditdel, name='creditdel'),
    url(r'^creditdeleted/$',
        genrender,
        kwargs={
            'template': 'hsp_creditdeleted.html',
            'page_title': 'Smazání splátky'},
        name='creditdeleted'),
    url(r'^balanceform/(\d+)/$', balanceform, name='balanceform'),
    url(r'^balanceform/$', balanceform, name='balanceform'),
    url(r'^balancedel/(\d+)/$', balancedel, name='balancedel'),
    url(r'^balancedeleted/$',
        genrender,
        kwargs={
            'template': 'hsp_balancedeleted.html',
            'page_title': 'Smazání kontrolního bodu'},
        name='balancedeleted'),
    url(r'^fxrateform/(\d+)/$', fxrateform, name='fxrateform'),
    url(r'^fxrateform/$', fxrateform, name='fxrateform'),
    url(r'^fxratedel/(\d+)/$', fxratedel, name='fxratedel'),
    url(r'^fxratedeleted/$',
        genrender,
        kwargs={
            'template': 'hsp_fxratedeleted.html',
            'page_title': 'Smazání kursu'},
        name='fxratedeleted'),
]
