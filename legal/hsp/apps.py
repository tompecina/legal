# -*- coding: utf-8 -*-
#
# hsp/apps.py
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

from django.apps import AppConfig


class HspConfig(AppConfig):

    name = 'legal.hsp'
    verbose_name = 'Historie složené pohledávky'
    version = '1.7'

    @staticmethod
    def stat():
        from legal.common.utils import LOGGER
        from legal.common.models import Asset
        LOGGER.debug('Partial statistics generated')
        return (
            (
                'Počet položek v tabulce Asset',
                Asset.objects.filter(assetid__startswith=HspConfig.name.upper()).count()),
        )
