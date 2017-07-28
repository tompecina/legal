# -*- coding: utf-8 -*-
#
# lht/views.py
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
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.apps import apps
from common.utils import pd, tod, odp, getbutton, logger, between
from common.glob import wn, inerr_short
from lht.glob import MIN_DATE, MAX_DATE, UNC_DATE
from lht.forms import MainForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version

class Result:

    def __init__(self, msg=None, res_date=None, bus_date=None, unc=False):
        self.msg = msg
        self.res_date = res_date
        self.bus_date = bus_date
        self.unc = unc


def calc(beg, dur, unit):

    OUT_MSG = \
        'Výsledek musí být mezi {} a {}'.format(pd(MIN_DATE), pd(MAX_DATE))

    if not between(MIN_DATE, beg, MAX_DATE):
        return Result(
            'Počátek musí být mezi {} a {}'.format(pd(MIN_DATE), pd(MAX_DATE)))

    if dur > 0:
        offset = odp
    else:
        offset = -odp

    if unit == 'd':
        res = beg + timedelta(days=dur)

    elif unit == 'w':
        res = beg + timedelta(weeks=dur)

    elif unit in ['m', 'y']:
        if unit == 'y':
            dur *= 12
        day = beg.day
        month = beg.month + dur - 1
        year = beg.year + (month // 12)
        month = (month % 12) + 1
        rng = monthrange(year, month)[1]
        if day > rng:
            day = rng
        if not between(MIN_DATE.year, year, MAX_DATE.year):
            return Result(OUT_MSG)
        res = date(year, month, day)
        
    elif unit == 'b':
        res = beg
        for _loop in range(abs(dur)):
            res += offset
            while tod(res):
                res += offset

    else:
        return Result('Neznámá jednotka')

    bus = res
    if unit != 'b':
        while tod(bus):
            bus += offset

    if not between(MIN_DATE, bus, MAX_DATE):
        return Result(OUT_MSG)

    unc = min(res, bus) < UNC_DATE or (beg < UNC_DATE and unit == 'b')

    return Result(None, res, bus, unc)


@require_http_methods(['GET', 'POST'])
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    today = date.today()

    messages = []

    if request.method == 'GET':
        f = MainForm()
    else:
        f = MainForm(request.POST)
        b = getbutton(request)
        if b == 'set_beg_date':
            f.data = f.data.copy()
            f.data['beg_date'] = today
        elif f.is_valid():
            cd = f.cleaned_data
            beg_date = cd['beg_date']
            preset = cd['preset']
            if preset == 'none':
                dur = cd['dur']
                unit = cd['unit']
            else:
                dur = int(preset[1:])
                unit = preset[0]

            res = calc(beg_date, dur, unit)

            if res.msg:
                messages = [[res.msg, None]]

            else:
                if res.res_date != res.bus_date:
                    messages.append(
                        ['{} není pracovní den'.format(
                            pd(res.res_date)), None])

                messages.append([
                    '{} {}'.format(
                        wn[res.bus_date.weekday()],
                        pd(res.bus_date)),
                     'msg-res'])

                if res.unc:
                    messages.append([
                        '(evidence pracovních dnů v tomto období není úplná)',
                        'msg-note'])

        else:
            logger.debug('Invalid form', request)
            messages = [[inerr_short, None]]

    return render(request,
                  'lht_main.html',
                  {'app': APP,
                   'page_title': 'Konec lhůty',
                   'messages': messages,
                   'f': f})
