# -*- coding: utf-8 -*-
#
# common/apps.py
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

from datetime import datetime, timedelta
from django.apps import AppConfig


class CommonConfig(AppConfig):

    name = 'common'
    verbose_name = 'Společné funkce'
    version = None

    @staticmethod
    def stat():
        from django.contrib.auth.models import User
        from .utils import logger
        from .models import PwResetLink, Preset
        now = datetime.now()
        logger.debug('Partial statistics generated')
        return (
            (
                'Počet uživatelů',
                User.objects.count()),
            (
                'Počet nových uživatelů za posledních 24 hodin',
                User.objects.filter(
                    date_joined__gte=(now - timedelta(hours=24))).count()),
            (
                'Počet nových uživatelů za poslední týden',
                User.objects.filter(
                    date_joined__gte=(now - timedelta(weeks=1))).count()),
            (
                'Počet nových uživatelů za poslední měsíc',
                User.objects.filter(
                    date_joined__gte=(now - timedelta(days=30))).count()),
            (
                'Počet dočasných linků pro obnovení hesla',
                PwResetLink.objects.count()),
            (
                'Počet záznamů v tabulce Preset',
                Preset.objects.count()),
        )

    @staticmethod
    def userinfo(user):
        from common.utils import logger
        logger.debug('Partial user information generated')
        return (
            (
                'Uživatelské jméno',
                user.username),
            (
                'Jméno',
                user.first_name if user.first_name else ''),
            (
                'Příjmení',
                user.last_name if user.last_name else ''),
            (
                'E-mail',
                '<a href="mailto:{0}">{0}</a>'.format(user.email)
                if user.email else ''),
            (
                'Datum založení účtu',
                '{:%d.%m.%Y}'.format(user.date_joined)),
        )
