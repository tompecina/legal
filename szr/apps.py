# -*- coding: utf-8 -*-
#
# szr/apps.py
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

from django.apps import AppConfig
from datetime import datetime, timedelta

class SzrConfig(AppConfig):
    name = 'szr'
    verbose_name = 'Sledování změn v řízení'
    version = '1.0'

    def stat(self):
        from .models import Court, Proceedings
        now = datetime.now()
        return [
            [
                'Počet soudů',
                Court.objects.count()],
            [
                'Z toho okresních soudů',
                Court.objects.filter(reports__isnull=False).count()],
            [
                'Počet sledovaných řízení',
                Proceedings.objects.count()],
            [
                'Počet nových sledovaných řízení za posledních 24 hodin',
                Proceedings.objects.filter(timestamp__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových sledovaných řízení za poslední týden',
                Proceedings.objects.filter(timestamp__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových sledovaných řízení za poslední měsíc',
                Proceedings.objects.filter(timestamp__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet sledovaných řízení pro příští notifikaci',
                Proceedings.objects.filter(notify=1).count()],
        ]
