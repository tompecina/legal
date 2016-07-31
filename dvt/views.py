# -*- coding: utf-8 -*-
#
# dvt/views.py
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
from datetime import date, timedelta
from calendar import monthrange
from common.utils import pd
from common.glob import inerr_short
from .forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

def calc(beg_date, years, months, days):
    y = beg_date.year
    m = beg_date.month
    d = beg_date.day
    y += years
    m += months
    y += ((m - 1) // 12)
    m = (((m - 1) % 12) + 1)
    d = min(d, monthrange(y, m)[1])
    return pd(date(y, m, d) + timedelta(days=days))

@require_http_methods(['GET', 'POST'])
def mainpage(request):
    messages = []

    if request.method == 'GET':
        f = MainForm()

    else:
        f = MainForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            beg_date = cd['beg_date']
            years = (cd['years'] if cd['years'] else 0)
            months = (cd['months'] if cd['months'] else 0)
            days = (cd['days'] if cd['days'] else 0)

            messages.append(
                [('Trest skončí: ' + calc(beg_date, years, months, days)),
                 'font-size: 115%; font-weight: bold; margin-bottom: 3px;'])
            messages.append(
                [('Třetina trestu: ' + \
                  calc(beg_date,
                       (years // 3),
                       (((years % 3) * 4) + (months // 3)),
                       (((months % 3) * 10) + (days // 3)))),
                 'margin-bottom: 2px;'])
            messages.append(
                [('Polovina trestu: ' + \
                  calc(beg_date,
                       (years // 2),
                       (((years % 2) * 6) + (months // 2)),
                       (((months % 2) * 15) + (days // 2)))),
                 'margin-bottom: 2px;'])
            messages.append(
                [('Dvě třetiny trestu: ' + \
                  calc(beg_date,
                       ((years * 2) // 3),
                       ((((years * 2) % 3) * 4) + ((months * 2) // 3)),
                       ((((months * 2) % 3) * 10) + ((days * 2) // 3)))),
                 None])


        else:
            messages = [[inerr_short, None]]

    return render(request,
                  'dvt_main.html',
                  {'app': APP,
                   'f': f,
                   'messages': messages,
                   'page_title': 'Doba výkonu trestu'})
