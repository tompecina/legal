# -*- coding: utf-8 -*-
#
# psj/apps.py
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

class PsjConfig(AppConfig):
    name = 'psj'
    verbose_name = 'Přehled soudních jednání'
    version = '1.1'

    def stat(self):
        from common.utils import logger
        from .models import Courtroom, Party, Judge, Form, Hearing, Task
        now = datetime.now()
        logger.debug('Partial statistics generated')
        return [
            [
                'Počet jednacích síní',
                Courtroom.objects.count()],
            [
                'Počet řešitelů',
                Judge.objects.count()],
            [
                'Počet druhů jednání',
                Form.objects.count()],
            [
                'Počet účastníků',
                Party.objects.count()],
            [
                'Počet nových účastníků za posledních 24 hodin',
                Party.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových účastníků za poslední týden',
                Party.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových účastníků za poslední měsíc',
                Party.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet jednání',
                Hearing.objects.count()],
            [
                'Počet nových jednání za posledních 24 hodin',
                Hearing.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových jednání za poslední týden',
                Hearing.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových jednání za poslední měsíc',
                Hearing.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet položek v tabulce Task',
                Task.objects.count()],
            [
                'Počet položek v tabulce Task starších než 12 hodin',
                Task.objects.filter(timestamp_add__lt=(now - \
                    timedelta(hours=12))).count()],
            [
                'Počet položek v tabulce Task starších než 24 hodin',
                Task.objects.filter(timestamp_add__lt=(now - \
                    timedelta(hours=24))).count()],
        ]
