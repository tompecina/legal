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

from datetime import date
from django.apps import apps
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from common.utils import getbutton, fdt, famt, unrequire, LocalFloat, logger
from common.glob import INERR_SHORT
from common.fields import AmountField
from cnb.utils import get_fx_rate, get_mpi_rate
from cnb.forms import MainForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    logger.debug(
        'Main page accessed using method ' + request.method,
        request,
        request.POST)

    rate_desc = {
        'DISC': 'Diskontní sazba',
        'LOMB': 'Lombardní sazba',
        'REPO': 'Repo sazba pro dvoutýdenní operace',
    }
    messages = []
    today = date.today()
    AmountField.rounding = 2

    if request.method == 'GET':
        form = MainForm()
    else:
        form = MainForm(request.POST)
        button = getbutton(request)
        if button in ('set_fx_date', 'set_mpi_date'):
            unrequire(form, ('fx_date', 'basis', 'mpi_date'))
            form.data = form.data.copy()
            if button == 'set_fx_date':
                form.data['fx_date'] = today
            else:
                form.data['mpi_date'] = today
        else:
            fxr = button in ('show_fx', 'conv_from', 'conv_to')
            if button == 'show_fx':
                unrequire(form, ('basis', 'mpi_date'))
            elif fxr:
                unrequire(form, ('mpi_date',))
            else:
                unrequire(form, ('fx_date', 'basis'))
            if form.is_valid():
                cld = form.cleaned_data
                if fxr:
                    curr = cld['curr']
                    fx_date = cld['fx_date']
                    rate, qty, dreq, msg = get_fx_rate(curr, fx_date)
                    if msg:
                        messages = [(msg, None)]
                    elif button == 'show_fx':
                        messages.append(
                            ('{:d} {} = {:.3f} CZK'.format(
                                qty,
                                curr,
                                LocalFloat(rate)),
                             'msg-res1'))
                        messages.append(
                            ('(Kurs vyhlášený ke dni: {})'.format(fdt(dreq)),
                             'msg-note'))
                    else:
                        basis = cld['basis']
                        if button == 'conv_from':
                            messages.append(
                                ('{} {} = {} CZK'.format(
                                    famt(basis),
                                    curr,
                                    famt(basis * rate / qty)),
                                 'msg-res2'))
                        else:
                            messages.append(
                                ('{} CZK = {} {}'.format(
                                    famt(basis),
                                    famt(basis * qty / rate),
                                    curr),
                                 'msg-res2'))
                        messages.append(
                            ('{:d} {} = {:.3f} CZK'.format(
                                qty,
                                curr,
                                LocalFloat(rate)),
                             None))
                        messages.append(
                            ('(Kurs vyhlášený ke dni: {})'.format(fdt(dreq)),
                             'msg-note'))
                else:
                    mpi_date = cld['mpi_date']
                    rate, msg = get_mpi_rate(button, mpi_date)
                    if msg:
                        messages = [(msg, None)]
                    else:
                        messages.append(
                            ('{} platná ke dni {}:'.format(
                                rate_desc[button], fdt(mpi_date)),
                             None))
                        messages.append(
                            ('{:.2f} %'.format(LocalFloat(rate)),
                             'msg-res0'))
            else:
                logger.debug('Invalid form', request)
                messages = [(INERR_SHORT, None)]

    return render(request,
                  'cnb_main.html',
                  {'app': APP,
                   'form': form,
                   'messages': messages,
                   'page_title': 'Kursy a sazby ČNB'})
