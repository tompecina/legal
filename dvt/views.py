# -*- coding: utf-8 -*-
#
# dvt/views.py
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

from datetime import date, timedelta
from calendar import monthrange

from django.views.decorators.http import require_http_methods
from django.apps import apps

from common.glob import INERR_SHORT
from common.utils import fdt, LOGGER, render
from dvt.forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

def calc(beg_date, years, months, days):
    year = beg_date.year
    month = beg_date.month
    day = beg_date.day
    year += years
    month += months
    year += (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(day, monthrange(year, month)[1])
    return fdt(date(year, month, day) + timedelta(days=days))

@require_http_methods(('GET', 'POST'))
def mainpage(request):

    LOGGER.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    messages = []

    if request.method == 'GET':
        form = MainForm()

    else:
        form = MainForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            beg_date = cld['beg_date']
            years = (cld['years'] if cld['years'] else 0)
            months = (cld['months'] if cld['months'] else 0)
            days = (cld['days'] if cld['days'] else 0)

            messages.append(
                ('Trest skončí: {}'.format(calc(
                    beg_date,
                    years, months,
                    days)),
                 'msg-res'))
            messages.append(
                ('Třetina trestu: {}'.format(calc(
                    beg_date,
                    years // 3,
                    ((years % 3) * 4) + (months // 3),
                    ((months % 3) * 10) + (days // 3))),
                 'msg-normal'))
            messages.append(
                ('Polovina trestu: {}'.format(calc(
                    beg_date,
                    years // 2,
                    ((years % 2) * 6) + (months // 2),
                    ((months % 2) * 15) + (days // 2))),
                 'msg-normal'))
            messages.append(
                ('Dvě třetiny trestu: {}'.format(calc(
                    beg_date,
                    (years * 2) // 3,
                    (((years * 2) % 3) * 4) + ((months * 2) // 3),
                    (((months * 2) % 3) * 10) + ((days * 2) // 3))),
                 None))


        else:
            LOGGER.debug('Invalid form', request)
            messages = [(INERR_SHORT, None)]

    return render(
        request,
        'dvt_main.html',
        {'app': APP,
         'form': form,
         'messages': messages,
         'page_title': 'Doba výkonu trestu'})
