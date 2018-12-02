# -*- coding: utf-8 -*-
#
# uds/apps.py
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


class UdsConfig(AppConfig):

    name = 'legal.uds'
    verbose_name = 'Archiv úřední desky soudů a SZ'
    version = '1.1'

    @staticmethod
    def stat():
        from legal.common.utils import LOGGER
        from legal.uds.models import Publisher, Agenda, Document, File, Retrieved
        now = datetime.now()
        LOGGER.debug('Partial statistics generated')
        return (
            (
                'Počet soudů a státních zastupitelství',
                Publisher.objects.count()),
            (
                'Z toho soudů',
                Publisher.objects.filter(type='SOUD').count()),
            (
                'Z toho státních zastupitelství',
                Publisher.objects.filter(type='ZAST').count()),
            (
                'Z toho nejvyšších a vrchních',
                Publisher.objects.filter(high=True).count()),
            (
                'Z toho krajských',
                Publisher.objects.filter(high=False, reports__isnull=True).count()),
            (
                'Z toho okresních',
                Publisher.objects.filter(reports__isnull=False).count()),
            (
                'Z toho krajských poboček',
                Publisher.objects.filter(subsidiary_region=True).count()),
            (
                'Z toho okresních poboček',
                Publisher.objects.filter(subsidiary_county=True).count()),
            (
                'Počet agend',
                Agenda.objects.count()),
            (
                'Počet dokumentů',
                Document.objects.count()),
            (
                'Počet dokumentů přidaných za posledních 24 hodin',
                Document.objects.filter(timestamp_add=(now - timedelta(hours=24))).count()),
            (
                'Počet dokumentů přidaných za poslední týden',
                Document.objects.filter(timestamp_add__gte=(now - timedelta(weeks=1))).count()),
            (
                'Počet dokumentů přidaných za poslední měsíc',
                Document.objects.filter(timestamp_add__gte=(now - timedelta(days=30))).count()),
            (
                'Počet souborů',
                File.objects.count()),
            (
                'Počet souborů přidaných za posledních 24 hodin',
                File.objects.filter(document__timestamp_add__gte=(now - timedelta(hours=24))).count()),
            (
                'Počet souborů přidaných za poslední týden',
                File.objects.filter(document__timestamp_add__gte=(now - timedelta(weeks=1))).count()),
            (
                'Počet souborů přidaných za poslední měsíc',
                File.objects.filter(document__timestamp_add__gte=(now - timedelta(days=30))).count()),
            (
                'Počet osob pro příští notifikaci',
                Retrieved.objects.count()),
        )
