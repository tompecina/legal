# -*- coding: utf-8 -*-
#
# kos/views.py
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

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.apps import apps
from datetime import date
from math import floor, ceil
from common.utils import getbutton, formam, p2c
from common.glob import inerr_short
from cnb.main import getFXrate
from .forms import MainForm
from .models import Preset

APP = __package__

APPVERSION = apps.get_app_config(APP).version

@require_http_methods(['GET', 'POST'])
def mainpage(request):
    messages = []

    if request.method == 'GET':
        f = MainForm()
    else:
        dual = (getbutton(request) == 'dual')
        f = MainForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            netincome = cd['netincome']
            deps = cd['deps']
            if cd['partner'] or dual:
                deps += 1
            subs = cd['subs']
            apt = cd['apt']
            vat = cd['vat']
            if vat:
                vatrate = float(cd['vatrate'])
            if dual:
                netincome2 = cd['netincome2']
                deps2 = cd['deps2'] + 1
                fee = cd['fee2']
                exp = cd['exp2']
                messages.append([
                    'Kalkulace pro společný návrh manželů',
                    'font-size: 125%; font-weight: bold; margin-bottom: 8px;'])
            else:
                fee = cd['fee']
                exp = cd['exp']
                messages.append([
                    'Kalkulace pro samostatného dlužníka',
                    'font-size: 125%; font-weight: bold; margin-bottom: 8px;'])
            lim = subs + apt
            prot = lim * (2.0 / 3.0)
            messages.append([
                ('Nezabavitelná částka: %s Kč' % formam(round(prot))),
                None])
            basis1 = ceil(prot * (1.0 + (deps / 4.0)))
            rem = max((netincome - basis1), 0.0)
            if rem > lim:
                rep = rem - lim
                rem = lim
            else:
                rep = 0
            rem = (rem // 3) * 3
            rep += (rem * 2) // 3
            if dual:
                totnetincome = netincome + netincome2
                basis2 = ceil(prot * (1.0 + (deps2 / 4.0)))
                messages.append([
                    ('Celková základní částka pro 1. manžela: %s Kč' % \
                     formam(round(basis1))),
                    None])
                messages.append([
                    ('Celková základní částka pro 2. manžela: %s Kč' % \
                     formam(round(basis2))),
                    None])
                rem2 = max((netincome2 - basis2), 0.0)
                if rem2 > lim:
                    rep2 = rem2 - lim
                    rem2 = lim
                else:
                    rep2 = 0
                rem2 = (rem2 // 3) * 3
                rep2 += (rem2 * 2) // 3
                rep += rep2
            else:
                totnetincome = netincome
                messages.append([
                    ('Celková základní částka: %s Kč' % formam(round(basis1))),
                    None])
            messages.append([
                ('Výše měsíční splátky: %s Kč' % formam(round(rep))),
                'margin-top: 8px;'])
            messages.append([
                ('Zůstatek ze mzdy: %s Kč' % formam(round(totnetincome - rep))),
                None])
            tru = fee + exp
            if vat:
                tru *= 1.0 + (vatrate / 100.0)
            messages.append([
                ('Měsíční poplatky insolvenčnímu správci: %s Kč' % \
                 formam(round(tru))),
                None])
            rep = max((rep - tru), 0.0)
            messages.append([
                ('Měsíční splátka věřitelům: %s Kč' % formam(round(rep))),
                None])
            tot = 5 * 12 * rep
            messages.append([
                ('Celková výše splátek věřitelům za 5 let: %s Kč' % \
                 formam(round(tot))),
                None])
            messages.append([
                'Pohledávky uspokojené do výše 30 %:',
                'margin-top: 8px;'])
            messages.append([
                ('%s Kč' % formam(round(tot / 0.3))),
                'font-size: 110%; font-weight: bold; margin-top: 2px;'])
        else:
            messages = [[inerr_short, None]]

    return render(request,
                  'kos_mainpage.html',
                  {'app': APP,
                   'page_title': 'Kalkulace splátek při oddlužení',
                   'messages': messages,
                   'f': f})
