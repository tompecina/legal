# -*- coding: utf-8 -*-
#
# kos/views.py
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

from math import ceil

from django.views.decorators.http import require_http_methods
from django.apps import apps

from legal.common.glob import INERR_SHORT
from legal.common.utils import getbutton, famt, LOGGER, render
from legal.kos.forms import MainForm


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    messages = []

    if request.method == 'GET':
        form = MainForm()
    else:
        dual = getbutton(request) == 'dual'
        form = MainForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            netincome = cld['netincome']
            deps = cld['deps']
            if cld['partner'] or dual:
                deps += 1
            subs = cld['subs']
            apt = cld['apt']
            vat = cld['vat']
            if vat:
                vatrate = float(cld['vatrate'])
            if dual:
                netincome2 = cld['netincome2']
                deps2 = cld['deps2'] + 1
                fee = cld['fee2']
                exp = cld['exp2']
                messages.append(('Kalkulace pro společný návrh manželů', 'header'))
            else:
                fee = cld['fee']
                exp = cld['exp']
                messages.append(('Kalkulace pro samostatného dlužníka', 'header'))
            lim = subs + apt
            prot = lim * 2 / 3
            messages.append(('Nezabavitelná částka: {} Kč'.format(famt(round(prot))), None))
            basis1 = ceil(prot * (1 + (deps / 4)))
            rem = max(netincome - basis1, 0)
            if rem > lim:
                rep = rem - lim
                rem = lim
            else:
                rep = 0
            rem = (rem // 3) * 3
            rep += (rem * 2) // 3
            if dual:
                totnetincome = netincome + netincome2
                basis2 = ceil(prot * (1 + (deps2 / 4)))
                messages.append(('Celková základní částka pro 1. manžela: {} Kč'.format(famt(round(basis1))), None))
                messages.append(('Celková základní částka pro 2. manžela: {} Kč'.format(famt(round(basis2))), None))
                rem2 = max(netincome2 - basis2, 0)
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
                messages.append(('Celková základní částka: {} Kč'.format(famt(round(basis1))), None))
            messages.append(('Výše měsíční splátky: {} Kč'.format(famt(round(rep))), 'gap'))
            messages.append(('Zůstatek ze mzdy: {} Kč'.format(famt(round(totnetincome - rep))), None))
            tru = fee + exp
            if vat:
                tru *= 1 + (vatrate / 100)
            messages.append(('Měsíční poplatky insolvenčnímu správci: {} Kč'.format(famt(round(tru))), None))
            rep = max(rep - tru, 0)
            messages.append(('Měsíční splátka věřitelům: {} Kč'.format(famt(round(rep))), None))
            tot = 5 * 12 * rep
            messages.append(('Celková výše splátek věřitelům za 5 let: {} Kč'.format(famt(round(tot))), None))
            messages.append(('Pohledávky uspokojené do výše 30 %:', 'gap'))
            messages.append(('{} Kč'.format(famt(round(tot / .3))), 'total'))
        else:
            LOGGER.debug('Invalid form', request)
            messages = [(INERR_SHORT, None)]

    return render(
        request,
        'kos_mainpage.xhtml',
        {'app': APP,
         'page_title': 'Kalkulace splátek při oddlužení',
         'messages': messages,
         'form': form})
