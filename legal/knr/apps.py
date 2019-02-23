# -*- coding: utf-8 -*-
#
# knr/apps.py
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

from django.apps import AppConfig


class KnrConfig(AppConfig):

    name = 'legal.knr'
    verbose_name = 'Náklady řízení'
    version = '1.10'

    @staticmethod
    def stat():
        from legal.common.utils import LOGGER
        from legal.common.models import Asset
        from legal.knr.models import Place, Car, Formula, Rate
        LOGGER.debug('Partial statistics generated')
        return (
            (
                'Počet míst',
                Place.objects.count()),
            (
                'Počet vozidel',
                Car.objects.count()),
            (
                'Počet předpisů',
                Formula.objects.count()),
            (
                'Počet sazeb',
                Rate.objects.count()),
            (
                'Počet položek v tabulce Asset',
                Asset.objects.filter(assetid__startswith=KnrConfig.name.upper()).count()),
        )

    @staticmethod
    def userinfo(user):
        from legal.common.utils import LOGGER
        from legal.knr.models import Place, Car, Formula
        LOGGER.debug('Partial user information generated')
        return (
            (
                'Počet míst',
                Place.objects.filter(uid=user).count()),
            (
                'Počet vozidel',
                Car.objects.filter(uid=user).count()),
            (
                'Počet předpisů',
                Formula.objects.filter(uid=user).count()),
        )
