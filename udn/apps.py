# -*- coding: utf-8 -*-
#
# udn/apps.py
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


class UdnConfig(AppConfig):

    name = 'udn'
    verbose_name = 'Archiv úřední desky NSS'
    version = '1.1'

    @staticmethod
    def stat():
        from common.utils import logger
        from .models import Agenda, Party, Decision
        now = datetime.now()
        logger.debug('Partial statistics generated')
        return [
            [
                'Počet oblastí',
                Agenda.objects.count()],
            [
                'Počet účastníků řízení',
                Party.objects.count()],
            [
                'Počet nových účastníků řízení za posledních 24 hodin',
                Party.objects.filter(
                    timestamp_add__gte=(now - timedelta(hours=24))).count()],
            [
                'Počet nových účastníků řízení za poslední týden',
                Party.objects.filter(
                    timestamp_add__gte=(now - timedelta(weeks=1))).count()],
            [
                'Počet nových účastníků řízení za poslední měsíc',
                Party.objects.filter(
                    timestamp_add__gte=(now - timedelta(days=30))).count()],
            [
                'Počet rozhodnutí',
                Decision.objects.count()],
            [
                'Počet nových rozhodnutí za posledních 24 hodin',
                Decision.objects.filter(
                    timestamp_add__gte=(now - timedelta(hours=24))).count()],
            [
                'Počet nových rozhodnutí za poslední týden',
                Decision.objects.filter(
                    timestamp_add__gte=(now - timedelta(weeks=1))).count()],
            [
                'Počet nových rozhodnutí za poslední měsíc',
                Decision.objects.filter(
                    timestamp_add__gte=(now - timedelta(days=30))).count()],
            [
                'Počet neúplných rozhodnutí',
                Decision.objects.filter(anonfilename='').count()],
            [
                'Počet neúplných rozhodnutí starších než 30 dnů',
                Decision.objects.filter(
                    anonfilename='',
                    date__lt=(now - timedelta(days=30))).count()],
            [
                'Počet neúplných rozhodnutí starších než 60 dnů',
                Decision.objects.filter(
                    anonfilename='',
                    date__lt=(now - timedelta(days=60))).count()],
            [
                'Počet neúplných rozhodnutí starších než 90 dnů',
                Decision.objects.filter(
                    anonfilename='',
                    date__lt=(now - timedelta(days=90))).count()],
            [
                'Počet neúplných rozhodnutí starších než 1 rok',
                Decision.objects.filter(
                    anonfilename='',
                    date__lt=(now - timedelta(days=365))).count()],
        ]
