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

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.apps import apps
from datetime import date
from common.utils import (
    pd, tod, ply, plm, ydconvs, mdconvs, yfactor, mfactor, odp, grammar,
    getbutton, unrequire, Lf, logger)
from common.glob import inerr_short, GR_D, GR_B, GR_M, GR_Y
from .forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

@require_http_methods(['GET', 'POST'])
def mainpage(request):

    logger.debug(
        'Main page accessed using method ' + request.method,
        request,
        request.POST)

    today = date.today()
    messages = []

    if request.method == 'GET':
        f = MainForm()
    else:
        f = MainForm(request.POST)
        b = getbutton(request)
        if b in ['set_beg_date', 'set_end_date']:
            unrequire(f, ['beg_date', 'end_date'])
            f.data = f.data.copy()
            if b == 'set_beg_date':
                f.data['beg_date'] = today
            else:
                f.data['end_date'] = today
        elif f.is_valid():
            cd = f.cleaned_data
            beg_date = cd['beg_date']
            end_date = cd['end_date']
            if beg_date >= end_date:
                messages.append(['Počátek musí předcházet konci', None])
            else:
                messages.append(['{} → {}'.format(pd(beg_date), pd(end_date)),
                                 'msg-header'])

                messages.append(
                    [grammar((end_date - beg_date).days, GR_D), None])

                if beg_date.year >= 1991:
                    t = beg_date + odp
                    n = 0
                    while t <= end_date:
                        if not tod(t):
                            n += 1
                        t += odp
                    messages.append([grammar(n, GR_B), None])

                ny = nm = nd = 0
                while True:
                    t = ply(beg_date, (ny + 1))
                    if t > end_date:
                        break
                    ny += 1
                r = ply(beg_date, ny)
                while True:
                    t = plm(r, (nm + 1))
                    if t > end_date:
                        break
                    nm += 1
                r = plm(r, nm)
                while r < end_date:
                    r += odp
                    nd += 1
                messages.append(
                    ['{} {} {}'.format(
                        grammar(ny, GR_Y),
                        grammar(nm, GR_M),
                        grammar(nd, GR_D)),
                     'msg-ymd'])

                for dconv in ydconvs:
                    messages.append(
                        ['{:.6f} let ({})'.format(
                            Lf(yfactor(beg_date, end_date, dconv)),
                            dconv),
                         'msg-y'])

                for dconv in mdconvs:
                    if dconv == mdconvs[0]:
                        messages.append(
                            ['{:.6f} měsíců ({})'.format(
                                Lf(mfactor(beg_date, end_date, dconv)),
                                dconv),
                             'msg-m1'])
                    else:
                        messages.append(
                            ['{:.6f} měsíců ({})'.format(
                                Lf(mfactor(beg_date, end_date, dconv)),
                                dconv),
                             'msg-m2'])

        else:
            logger.debug('Invalid form', request)
            messages = [[inerr_short, None]]

    return render(request, 'cin_main.html',
                  {'app': APP,
                   'f': f,
                   'messages': messages,
                   'page_title': 'Délka časového intervalu'})
