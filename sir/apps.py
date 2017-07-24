# -*- coding: utf-8 -*-
#
# sir/apps.py
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

class SirConfig(AppConfig):
    name = 'sir'
    verbose_name = 'Sledování změn v insolvenčních řízeních'
    version = '1.0'

    def stat(self):
        from common.utils import logger
        from .models import (
            DruhAdresy, Adresa, DruhRoleVRizeni, Osoba, Role, DruhStavRizeni,
            Vec, Counter, Transaction, Insolvency, Tracked)
        now = datetime.now()
        logger.debug('Partial statistics generated')
        return [
            [
                'Počet druhů adresy',
                DruhAdresy.objects.count()],
            [
                'Počet adres',
                Adresa.objects.count()],
            [
                'Počet nových adres za posledních 24 hodin',
                Adresa.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových adres za poslední týden',
                Adresa.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových adres za poslední měsíc',
                Adresa.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet rolí v řízení',
                DruhRoleVRizeni.objects.count()],
            [
                'Počet osob',
                Osoba.objects.count()],
            [
                'Počet nových osob za posledních 24 hodin',
                Osoba.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových osob za poslední týden',
                Osoba.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových osob za poslední měsíc',
                Osoba.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet rolí',
                Role.objects.count()],
            [
                'Počet nových rolí za posledních 24 hodin',
                Role.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových rolí za poslední týden',
                Role.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových rolí za poslední měsíc',
                Role.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet stavů řízení',
                DruhStavRizeni.objects.count()],
            [
                'Počet řízení',
                Vec.objects.count()],
            [
                'Z toho vyškrtnutých',
                Vec.objects.filter(datumVyskrtnuti__isnull=False).count()],
            [
                'Počet nových řízení za posledních 24 hodin',
                Vec.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových řízení za poslední týden',
                Vec.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových řízení za poslední měsíc',
                Vec.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet sledovaných řízení',
                Insolvency.objects.count()],
            [
                'Počet nových sledovaných řízení za posledních 24 hodin',
                Insolvency.objects.filter(timestamp_add__gte=(now - \
                    timedelta(hours=24))).count()],
            [
                'Počet nových sledovaných řízení za poslední týden',
                Insolvency.objects.filter(timestamp_add__gte=(now - \
                    timedelta(weeks=1))).count()],
            [
                'Počet nových sledovaných řízení za poslední měsíc',
                Insolvency.objects.filter(timestamp_add__gte=(now - \
                    timedelta(days=30))).count()],
            [
                'Počet řízení pro příští notifikaci',
                Tracked.objects.count()],
            [
                'Počet nezpracovaných transakcí',
                Transaction.objects.count()],
            [
                'Z toho chybných',
                Transaction.objects.filter(error=True).count()],
            [
                'Stav počitadla transakcí',
                Counter.objects.get(id='DL').number],
            [
                'Stav počitadla zpracovaných řízení',
                Counter.objects.get(id='PR').number],
        ]

    def userinfo(self, user):
        from common.utils import logger
        from .models import Insolvency
        logger.debug('Partial user information generated')
        return [
            [
                'Počet sledovaných insolvencí',
                Insolvency.objects.filter(uid=user).count()],
        ]
