# -*- coding: utf-8 -*-
#
# cin/views.py
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
from common.utils import pd, tod, ply, plm, ydconvs, mdconvs, yfactor, \
                         mfactor, odp, grammar, getbutton, unrequire, p2c, \
                         inerr_short
from .forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

GR_D = ('den', 'dny', 'dnů')
GR_B = ('pracovní den', 'pracovní dny', 'pracovních dnů')
GR_M = ('měsíc', 'měsíce', 'měsíců')
GR_Y = ('rok', 'roky', 'let')

@require_http_methods(['GET', 'POST'])
def mainpage(request):
    today = date.today()
    messages = []

    if request.method == 'GET':
        f = MainForm()
    else:
        f = MainForm(request.POST)
        b = getbutton(request)
        if b in ['set_beg', 'set_end']:
            unrequire(f, ['beg', 'end'])
            if b == 'set_beg':
                f.data['beg'] = today
            else:
                f.data['end'] = today
        elif f.is_valid():
            cd = f.cleaned_data
            beg = cd['beg']
            end = cd['end']
            if beg >= end:
                messages.append(['Počátek musí předcházet konci', None])
            else:
                messages.append([('%s → %s' % (pd(beg), pd(end))),
                                 'font-weight: bold; margin-bottom: 5px;'])

                messages.append([grammar((end - beg).days, GR_D), None])

                if beg.year >= 1991:
                    t = beg + odp
                    n = 0
                    while t <= end:
                        if not tod(t):
                            n += 1
                        t += odp
                    messages.append([grammar(n, GR_B), None])

                ny = nm = nd = 0
                while True:
                    t = ply(beg, (ny + 1))
                    if t > end:
                        break
                    ny += 1
                r = ply(beg, ny)
                while True:
                    t = plm(r, (nm + 1))
                    if t > end:
                        break
                    nm += 1
                r = plm(r, nm)
                while r < end:
                    r += odp
                    nd += 1
                messages.append(['%s %s %s' % (grammar(ny, GR_Y),
                                               grammar(nm, GR_M),
                                               grammar(nd, GR_D)),
                                 'margin-bottom: 12px;'])

                for dconv in ydconvs:
                    messages.append(
                        [p2c('%.6f' % yfactor(beg, end, dconv)) + \
                         ' let (' + dconv + \
                         ')', 'text-align: left; margin-left: 2em;'])

                for dconv in mdconvs:
                    if dconv == mdconvs[0]:
                        messages.append(
                            [p2c('%.6f' % mfactor(beg, end, dconv)) + \
                             ' měsíců (' + dconv + ')',
                             'text-align: left; margin-top: 8px; ' \
                             'margin-left: 2em;'])
                    else:
                        messages.append(
                            [p2c('%.6f' % mfactor(beg, end, dconv)) + \
                             ' měsíců (' + dconv + ')',
                             'text-align: left; margin-left: 2em;'])

        else:
            messages = [[inerr_short, None]]

    return render(request, 'cin_main.html',
                  {'app': APP,
                   'f': f,
                   'messages': messages,
                   'page_title': 'Délka časového intervalu'})
