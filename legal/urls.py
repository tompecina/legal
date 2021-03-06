# -*- coding: utf-8 -*-
#
# urls.py
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

from django.conf.urls import include, url
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import admin

from legal.settings import APPS
from legal.common.views import (
    home, robots, pwchange, userinfo, useradd, lostpw, resetpw, about, gdpr, stat, doc, genrender)


admin.autodiscover()


handler400 = 'legal.common.views.error400'
handler403 = 'legal.common.views.error403'
handler404 = 'legal.common.views.error404'
handler500 = 'legal.common.views.error500'


urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^robots\.txt$', robots),
    url(r'^accounts/pwchange/$', pwchange, name='pwchange'),
    url(r'^accounts/pwchanged/$',
        genrender,
        kwargs={
            'template': 'pwchanged.xhtml',
            'page_title': 'Změna hesla'},
        name='pwchanged'),
    url(r'^accounts/login/$',
        LoginView.as_view(
            template_name='login.xhtml',
            extra_context={'page_title': 'Přihlášení', 'suppress_login': True}),
        name='login'),
    url(r'^accounts/logout/$',
        LogoutView.as_view(
            template_name='logout.xhtml',
            extra_context={'page_title': 'Odhlášení'}),
        name='logout'),
    url(r'^accounts/user/$', userinfo, name='user'),
    url(r'^accounts/useradd/$', useradd, name='useradd'),
    url(r'^accounts/useradded/$',
        genrender,
        kwargs={
            'template': 'useradded.xhtml',
            'page_title': 'Registrace nového uživatele'},
        name='useradded'),
    url(r'^accounts/lostpw/$', lostpw, name='lostpw'),
    url(r'^accounts/resetpw/([0-9a-f]{32})/$', resetpw, name='resetpw'),
    url(r'^accounts/pwlinksent/$',
        genrender,
        kwargs={
            'template': 'pwlinksent.xhtml',
            'page_title': 'Obnovení hesla'},
        name='pwlinksent'),
    url(r'^about/$', about, name='about'),
    url(r'^gdpr/$', gdpr, name='gdpr'),
    url(r'^stat/$', stat, name='stat'),
    url(r'^doc/(.+)$', doc, name='doc'),
    url(r'^admin/', include((admin.site.urls[0], 'admin')))
] + [url('^{}/'.format(a), include(('legal.{}.urls'.format(a), a), namespace=a)) for a in APPS]
