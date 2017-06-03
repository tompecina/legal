# -*- coding: utf-8 -*-
#
# cnb/views.py
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
from datetime import date
from django.apps import apps
from common.utils import getbutton, pd, formam, unrequire, p2c, logger
from common.glob import inerr_short
from common.fields import AmountField
from .main import getFXrate, getMPIrate
from .forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

@require_http_methods(['GET', 'POST'])
def mainpage(request):

    logger.debug(
        'Main page accessed using method ' + request.method,
        request,
        request.POST)

    rate_desc = {'DISC': 'Diskontní sazba',
                 'LOMB': 'Lombardní sazba',
                 'REPO': 'Repo sazba pro dvoutýdenní operace'}
    messages = []
    today = date.today()
    AmountField.rounding = 2

    if request.method == 'GET':
        f = MainForm()
    else:
        f = MainForm(request.POST)
        b = getbutton(request)
        if b in ['set_fx_date', 'set_mpi_date']:
            unrequire(f, ['fx_date', 'basis', 'mpi_date'])
            f.data = f.data.copy()
            if b == 'set_fx_date':
                f.data['fx_date'] = today
            else:
                f.data['mpi_date'] = today
        else:
            fx = (b in ['show_fx', 'conv_from', 'conv_to'])
            if b == 'show_fx':
                unrequire(f, ['basis', 'mpi_date'])
            elif fx:
                unrequire(f, ['mpi_date'])
            else:
                unrequire(f, ['fx_date', 'basis'])
            if f.is_valid():
                cd = f.cleaned_data
                if fx:
                    curr = cd['curr']
                    fx_date = cd['fx_date']
                    rate, qty, dr, msg = getFXrate(curr, fx_date)
                    if msg:
                        messages = [[msg, None]]
                    elif b == 'show_fx':
                        messages.append(
                            [('%d %s = %s CZK' % \
                              (qty, curr, p2c("%.3f" % rate))),
                             'msg-res1'])
                        messages.append(
                            [('(Kurs vyhlášený ke dni: %s)' % pd(dr)),
                             'msg-note'])
                    else:
                        basis = cd['basis']
                        if b == 'conv_from':
                            messages.append(
                                [('%s %s = %s CZK' % \
                                  (formam(basis),
                                   curr,
                                   formam(basis * rate / qty))),
                                 'msg-res2'])
                        else:
                            messages.append(
                                [('%s CZK = %s %s' % \
                                  (formam(basis),
                                   formam(basis * qty / rate),
                                   curr)),
                                 'msg-res2'])
                        messages.append(
                            [('%d %s = %s CZK' % \
                              (qty, curr, p2c("%.3f" % rate))),
                             None])
                        messages.append(
                            [('(Kurs vyhlášený ke dni: %s)' % pd(dr)),
                             'msg-note'])
                else:
                    mpi_date = cd['mpi_date']
                    rate, msg = getMPIrate(b, mpi_date)
                    if msg:
                        messages = [[msg, None]]
                    else:
                        messages.append(
                            [('%s platná ke dni %s:' % \
                              (rate_desc[b], pd(mpi_date))),
                             None])
                        messages.append(
                            [p2c('%.2f %%' % rate),
                             'msg-res0'])
            else:
                logger.debug('Invalid form', request)
                messages = [[inerr_short, None]]

    return render(request,
                  'cnb_main.html',
                  {'app': APP,
                   'f': f,
                   'messages': messages,
                   'page_title': 'Kursy a sazby ČNB'})
