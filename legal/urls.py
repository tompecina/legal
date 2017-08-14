# -*- coding: utf-8 -*-
#
# urls.py
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

from django.conf.urls import include, url
from django.contrib.auth.views import LoginView
from django.contrib import admin

from legal.settings import APPS
from legal.common.views import (
    home, robots, pwchange, logout, userinfo, useradd, lostpw, resetpw, about, stat, genrender)


admin.autodiscover()


urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^robots\.txt$', robots),
    url(r'^accounts/pwchange/$', pwchange, name='pwchange'),
    url(r'^accounts/pwchanged/$',
        genrender,
        kwargs={
            'template': 'pwchanged.html',
            'page_title': 'Změna hesla'},
        name='pwchanged'),
    url(r'^accounts/login/$',
        LoginView.as_view(template_name='login.html'),
        name='login'),
    url(r'^accounts/logout/$', logout, name='logout'),
    url(r'^accounts/user/$', userinfo, name='user'),
    url(r'^accounts/useradd/$', useradd, name='useradd'),
    url(r'^accounts/useradded/$',
        genrender,
        kwargs={
            'template': 'useradded.html',
            'page_title': 'Registrace nového uživatele'},
        name='useradded'),
    url(r'^accounts/lostpw/$', lostpw, name='lostpw'),
    url(r'^accounts/resetpw/([0-9a-f]{32})/$', resetpw, name='resetpw'),
    url(r'^accounts/pwlinksent/$',
        genrender,
        kwargs={
            'template': 'pwlinksent.html',
            'page_title': 'Obnovení hesla'},
        name='pwlinksent'),
    url(r'^about/$', about, name='about'),
    url(r'^stat/$', stat, name='stat'),
    url(r'^admin/', include((admin.site.urls[0], 'admin')))
] + [url('^{}/'.format(a), include(('legal.{}.urls'.format(a), a), namespace=a)) for a in APPS]
