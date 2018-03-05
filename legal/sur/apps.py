# -*- coding: utf-8 -*-
#
# sur/apps.py
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

from datetime import datetime, timedelta

from django.apps import AppConfig


class SurConfig(AppConfig):

    name = 'legal.sur'
    verbose_name = 'Sledování účastníků řízení'
    version = '1.0'

    @staticmethod
    def stat():
        from legal.common.utils import LOGGER
        from legal.sur.models import Party, Found
        now = datetime.now()
        LOGGER.debug('Partial statistics generated')
        return (
            (
                'Počet účastníků řízení',
                Party.objects.count()),
            (
                'Počet nových účastníků řízení za posledních 24 hodin',
                Party.objects.filter(timestamp_add__gte=(now - timedelta(hours=24))).count()),
            (
                'Počet nových účastníků řízení za poslední týden',
                Party.objects.filter(timestamp_add__gte=(now - timedelta(weeks=1))).count()),
            (
                'Počet nových účastníků řízení za poslední měsíc',
                Party.objects.filter(timestamp_add__gte=(now - timedelta(days=30))).count()),
            (
                'Počet účastníků řízení pro příští notifikaci',
                Found.objects.count()),
        )

    @staticmethod
    def userinfo(user):
        from legal.common.utils import LOGGER
        from legal.sur.models import Party
        LOGGER.debug('Partial user information generated')
        return (
            (
                'Počet sledovaných účastníků',
                Party.objects.filter(uid=user).count()),
        )
