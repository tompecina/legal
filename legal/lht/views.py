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

from django.views.decorators.http import require_http_methods
from django.apps import apps

from legal.common.glob import WD_NAMES, INERR_SHORT, ODP, ODM, UNC_DATE
from legal.common.utils import fdt, holiday, getbutton, LOGGER, between, render
from legal.lht.glob import MIN_DATE, MAX_DATE, MIN_DUR, MAX_DUR
from legal.lht.forms import MainForm


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version


class Period:

    def __init__(self, beg, dur, unit):

        def out_msg():
            return 'Výsledek musí být mezi {} a {}'.format(fdt(MIN_DATE), fdt(MAX_DATE))

        self.beg = beg
        self.dur = dur
        self.unit = unit
        self.res = self.bus = self.unc = None

        self.error = True

        if not between(MIN_DATE, beg, MAX_DATE):
            self.msg = 'Počátek musí být mezi {} a {}'.format(fdt(MIN_DATE), fdt(MAX_DATE))
            return

        if not between(MIN_DUR, dur, MAX_DUR):
            self.msg = 'Délka musí být mezi {:d} a {:d}'.format(MIN_DUR, MAX_DUR)
            return

        offset = ODM if dur < 0 else ODP

        if unit == 'd':
            res = beg + timedelta(days=dur)

        elif unit == 'w':
            res = beg + timedelta(weeks=dur)

        elif unit in ('m', 'y'):
            if unit == 'y':
                dur *= 12
            month = beg.month + dur - 1
            year = beg.year + (month // 12)
            if not between(MIN_DATE.year, year, MAX_DATE.year):
                self.msg = out_msg()
                return
            month = (month % 12) + 1
            res = date(year, month, min(beg.day, monthrange(year, month)[1]))

        elif unit == 'b':
            res = beg
            for dummy in range(abs(dur)):
                res += offset
                while holiday(res):
                    res += offset
            while holiday(res):  # only needed for dur == 0
                res += offset

        else:
            self.msg = 'Neznámá jednotka'
            return

        bus = res
        if unit != 'b':
            while holiday(bus):
                bus += offset

        if not between(MIN_DATE, bus, MAX_DATE):
            self.msg = out_msg()
            return

        self.error = False
        self.msg = None
        self.res = res
        self.bus = bus
        self.unc = min(res, bus) < UNC_DATE or (beg < UNC_DATE and unit == 'b')


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
        if button == 'set_beg_date':
            form.data = form.data.copy()
            form.data['beg_date'] = today
        elif form.is_valid():
            cld = form.cleaned_data
            beg = cld['beg_date']
            preset = cld['preset']
            if preset == 'none':
                dur = cld['dur']
                unit = cld['unit']
            else:
                dur = int(preset[1:])
                unit = preset[0]

            per = Period(beg, dur, unit)

            if per.error:
                messages = [(per.msg, None)]

            else:
                if per.res != per.bus:
                    messages.append(('{} není pracovní den'.format(fdt(per.res)), None))

                messages.append(('{} {}'.format(WD_NAMES[per.bus.weekday()], fdt(per.bus)), 'msg-res'))

                if per.unc:
                    messages.append(('(evidence pracovních dnů v tomto období není úplná)', 'msg-note'))

        else:
            LOGGER.debug('Invalid form', request)
            messages = [(INERR_SHORT, None)]

    return render(request,
                  'lht_mainpage.html',
                  {'app': APP,
                   'page_title': 'Konec lhůty',
                   'messages': messages,
                   'form': form})
