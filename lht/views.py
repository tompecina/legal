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
from common.utils import pd, tod, getbutton, logger, between
from common.glob import wn, inerr_short, odp, odm
from lht.glob import MIN_DATE, MAX_DATE, UNC_DATE
from lht.forms import MainForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version

class Period:

    def __init__(self, beg, dur, unit):

        def out_msg():
            return 'Výsledek musí být mezi {} a {}' \
                .format(pd(MIN_DATE), pd(MAX_DATE))

        self.beg = beg
        self.dur = dur
        self.unit = unit
        self.res = self.bus = self.unc = None
        
        self.error = True

        if not between(MIN_DATE, beg, MAX_DATE):
            self.msg = 'Počátek musí být mezi {} a {}' \
                .format(pd(MIN_DATE), pd(MAX_DATE))
            return

        if dur >= 0:
            offset = odp
        else:
            offset = odm

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
            day = min(day, monthrange(year, month)[1])
            if not between(MIN_DATE.year, year, MAX_DATE.year):
                self.msg = out_msg()
                return
            res = date(year, month, day)

        elif unit == 'b':
            res = beg
            for dummy in range(abs(dur)):
                res += offset
                while tod(res):
                    res += offset
            while tod(res):  # needed only for dur == 0
                res += offset

        else:
            self.msg = 'Neznámá jednotka'
            return

        bus = res
        if unit != 'b':
            while tod(bus):
                bus += offset

        if not between(MIN_DATE, bus, MAX_DATE):
            self.msg = out_msg()
            return

        self.error = False
        self.msg = None
        self.res = res
        self.bus = bus
        self.unc = min(res, bus) < UNC_DATE \
            or (beg < UNC_DATE and unit == 'b')


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
            beg = cd['beg_date']
            preset = cd['preset']
            if preset == 'none':
                dur = cd['dur']
                unit = cd['unit']
            else:
                dur = int(preset[1:])
                unit = preset[0]

            per = Period(beg, dur, unit)

            if per.error:
                messages = [[per.msg, None]]

            else:
                if per.res != per.bus:
                    messages.append(
                        ['{} není pracovní den'.format(
                            pd(per.res)), None])

                messages.append([
                    '{} {}'.format(
                        wn[per.bus.weekday()],
                        pd(per.bus)),
                     'msg-per'])

                if per.unc:
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
