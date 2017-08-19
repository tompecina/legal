# -*- coding: utf-8 -*-
#
# cin/views.py
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

from datetime import date

from django.views.decorators.http import require_http_methods
from django.apps import apps

from legal.common.glob import (
    INERR_SHORT, GR_DAY, GR_BUSDAY, GR_MONTH, GR_YEAR, UNC_DATE)
from legal.common.utils import (
    fdt, holiday, ply, plm, YDCONVS, MDCONVS, yfactor, mfactor, ODP,
    grammar, getbutton, unrequire, LocalFloat, LOGGER, render)
from legal.cin.forms import MainForm


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    today = date.today()
    messages = []

    if request.method == 'GET':
        form = MainForm()
    else:
        form = MainForm(request.POST)
        button = getbutton(request)
        if button in ('set_beg_date', 'set_end_date'):
            unrequire(form, ('beg_date', 'end_date'))
            form.data = form.data.copy()
            form.data['{}_date'.format(button[4:7])] = today
        elif form.is_valid():
            cld = form.cleaned_data
            beg_date = cld['beg_date']
            end_date = cld['end_date']
            if beg_date >= end_date:
                messages.append(('Počátek musí předcházet konci', None))
            else:
                messages.append(('{} → {}'.format(fdt(beg_date), fdt(end_date)), 'header'))

                messages.append((grammar((end_date - beg_date).days, GR_DAY), None))

                if beg_date >= UNC_DATE:
                    temp = beg_date + ODP
                    num = 0
                    while temp <= end_date:
                        if not holiday(temp):
                            num += 1
                        temp += ODP
                    messages.append((grammar(num, GR_BUSDAY), None))

                nyear = nmonth = nday = 0
                while True:
                    temp = ply(beg_date, nyear + 1)
                    if temp > end_date:
                        break
                    nyear += 1
                res = ply(beg_date, nyear)
                while True:
                    temp = plm(res, nmonth + 1)
                    if temp > end_date:
                        break
                    nmonth += 1
                res = plm(res, nmonth)
                while res < end_date:
                    res += ODP
                    nday += 1
                messages.append(
                    ('{} {} {}'.format(grammar(nyear, GR_YEAR), grammar(nmonth, GR_MONTH), grammar(nday, GR_DAY)),
                     'ymd'))

                for dconv in YDCONVS:
                    messages.append(
                        ('{:.6f} let ({})'.format(LocalFloat(yfactor(beg_date, end_date, dconv)), dconv),
                         'year'))

                for dconv in MDCONVS:
                    if dconv == MDCONVS[0]:
                        messages.append(
                            ('{:.6f} měsíců ({})'.format(LocalFloat(mfactor(beg_date, end_date, dconv)), dconv),
                             'month1'))
                    else:
                        messages.append(
                            ('{:.6f} měsíců ({})'.format(LocalFloat(mfactor(beg_date, end_date, dconv)), dconv),
                             'month2'))

        else:
            LOGGER.debug('Invalid form', request)
            messages = [(INERR_SHORT, None)]

    return render(
        request,
        'cin_mainpage.html',
        {'app': APP,
         'form': form,
         'messages': messages,
         'page_title': 'Délka časového intervalu'})
