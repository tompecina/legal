# -*- coding: utf-8 -*-
#
# cnb/apps.py
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


class CnbConfig(AppConfig):

    name = 'legal.cnb'
    verbose_name = 'Kursy a sazby ČNB'
    version = '1.0'

    @staticmethod
    def stat():
        from legal.cnb.models import FXrate, MPIrate, MPIstat
        from legal.common.utils import LOGGER
        LOGGER.debug('Partial statistics generated')
        return (
            (
                'Počet kursových tabulek',
                FXrate.objects.count()),
            (
                'Počet historických úrokových sazeb',
                MPIrate.objects.count()),
            (
                'Počet aktuálních úrokových sazeb',
                MPIstat.objects.count()),
        )
