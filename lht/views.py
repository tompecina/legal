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
from common.utils import pd, tod, odp, getbutton, logger
from common.glob import wn, inerr_short
from lht.forms import MainForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version


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
            if beg_date.year < 1991:
                messages = [['Počátek musí být ≥1.1.1991', None]]
            else:
                preset = cd['preset']
                if preset == 'none':
                    dur = cd['dur']
                    unit = cd['unit']
                else:
                    dur = int(preset[1:])
                    unit = preset[0]
                if dur > 0:
                    o = odp
                else:
                    o = -odp
                if unit == 'd':
                    t = beg_date + timedelta(days=dur)
                elif unit == 'w':
                    t = beg_date + timedelta(weeks=dur)
                elif unit in ['m', 'y']:
                    if unit == 'y':
                        dur *= 12
                    d = beg_date.day
                    m = beg_date.month
                    y = beg_date.year
                    if dur > 0:
                        for _ in range(dur):
                            m += 1
                            if m > 12:
                                m = 1
                                y += 1
                    else:
                        for _ in range(-dur):
                            m -= 1
                            if not m:
                                m = 12
                                y -= 1
                    r = monthrange(y, m)[1]
                    if d > r:
                        d = r
                    t = date(y, m, d)
                else:
                    t = beg_date
                    for _ in range(abs(dur)):
                        t += o
                        while tod(t):
                            t += o

                if tod(t):
                    messages.append(
                        ['{} není pracovní den'.format(pd(t)), None])

                while tod(t):
                    t += o

                messages.append(
                    ['{} {}'.format(wn[t.weekday()], pd(t)),
                     'msg-res'])
                if t < date(1991, 1, 1):
                    messages.append(
                        ['(evidence pracovních dnů v tomto období '
                         'není úplná)',
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
