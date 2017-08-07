# -*- coding: utf-8 -*-
#
# sop/views.py
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

from math import floor, ceil

from django.views.decorators.http import require_http_methods
from django.apps import apps

from common.glob import INERR_SHORT
from common.utils import famt, LocalFloat, logger, render
from cnb.utils import get_fx_rate
from sop.forms import MainForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    logger.debug(
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
            basis = cld['basis']
            curr = cld['curr']
            model = int(cld['model'])
            opt = cld['opt']
            fx_info = ''
            if curr != 'CZK':
                fx_date = cld['fx_date']
                rate, qty, dummy, msg = get_fx_rate(curr, fx_date)
                if msg:
                    messages = [(msg, None)]
                else:
                    basis *= rate / qty
                    fx_info = '{:d} {} = {:.3f} CZK'.format(
                        qty,
                        curr,
                        LocalFloat(rate))
            if not messages:
                if opt == 'epr' and basis > 1000000:
                    messages = [('Nad limit pro EPR', None)]
                else:
                    if model < 4:
                        basis = int(floor(basis / 100) * 100)
                    else:
                        basis = int(ceil(basis / 10) * 10)
                    if opt == 'none' or (opt == 'nmu' and model == 1):
                        if model == 1:
                            if basis <= 15000:
                                sop = 600
                            else:
                                sop = basis / 25
                        else:
                            if basis <= 20000:
                                sop = 1000
                            elif basis <= 40000000:
                                sop = basis / 20
                            else:
                                sop = min(2000000 + ((basis - 40000000)
                                    / 100), 4100000)
                    elif opt == 'epr':
                        if model == 1:
                            if basis <= 15000:
                                sop = 300
                            else:
                                sop = basis / 50
                        elif model == 2:
                            if basis <= 20000:
                                sop = 800
                            else:
                                sop = basis / 25
                        else:
                            if basis <= 10000:
                                sop = 400
                            elif basis <= 20000:
                                sop = 800
                            else:
                                sop = basis / 25
                    elif opt == 'nmu':
                        if basis <= 200000:
                            sop = 2000
                        else:
                            sop = basis / 100
                    elif opt == 'vyz':
                        if model == 1:
                            if basis <= 30000:
                                sop = 300
                            else:
                                sop = min(basis / 100, 10000)
                        else:
                            if basis <= 50000:
                                sop = 500
                            else:
                                sop = min(basis / 100, 15000)
                    elif opt == 'vyk':
                        if model == 1:
                            if basis <= 15000:
                                sop = 300
                            else:
                                sop = min(basis / 50, 50000)
                        elif model == 2:
                            if basis <= 25000:
                                sop = 500
                            else:
                                sop = min(basis / 50, 75000)
                        else:
                            if basis <= 20000:
                                sop = 1000
                            elif basis <= 40000000:
                                sop = basis / 20
                            else:
                                sop = 2000000 + ((min(basis, 250000000)
                                    - 40000000) / 100)
                    elif opt == 'sm':
                        if model == 1:
                            if basis <= 15000:
                                sop = 300
                            else:
                                sop = min(basis / 50, 20000)
                        else:
                            if basis <= 25000:
                                sop = 500
                            else:
                                sop = min(basis / 50, 30000)
                    elif opt == 'inc':
                        if model == 1:
                            sop = 1000
                        else:
                            if basis <= 20000:
                                sop = 1000
                            else:
                                sop = basis / 20
                    else:
                        if model == 1:
                            if basis <= 20000:
                                sop = 200
                            else:
                                sop = basis / 100
                        else:
                            if basis <= 25000:
                                sop = 250
                            else:
                                sop = basis / 100
                    if model < 4:
                        sop = int(ceil(sop / 10) * 10)
                    if model == 1:
                        sop = min(sop, 1000000)
                    elif opt != 'none' and (opt != 'vyk' or model < 3):
                        sop = min(sop, 2000000)
                    messages.append(('Soudní poplatek:', None))
                    messages.append(
                        ('{} Kč'.format(famt(round(sop))),
                         'msg-amount'))
                    if fx_info:
                        messages.append((fx_info, 'msg-note'))
        else:
            logger.debug('Invalid form', request)
            messages = [(INERR_SHORT, None)]

    return render(request,
                  'sop_main.html',
                  {'app': APP,
                   'page_title': 'Soudní poplatek',
                   'messages': messages,
                   'form': form})
