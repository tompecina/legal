# -*- coding: utf-8 -*-
#
# sur/views.py
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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from common.utils import getbutton, grammar
from common.glob import inerr, GR_C, text_opts, text_opts_keys
from szr.forms import EmailForm
from .forms import PartyForm
from .models import Party
from .glob import MIN_LENGTH

APP = __package__

APPVERSION = apps.get_app_config(APP).version

@require_http_methods(['GET', 'POST'])
@login_required
def partyform(request, id=0):
    err_message = ''
    uid = request.user.id
    page_title = ('Úprava účastníka' if id else 'Nový účastník')
    btn = getbutton(request)
    if request.method == 'GET':
        if id:
            d = model_to_dict(get_object_or_404(Party, pk=id, uid=uid))
            d['party_opt'] = text_opts_keys[d['party_opt']]
            f = PartyForm(initial=d)
        else:
            f = PartyForm()
    elif btn == 'back':
        return redirect('sur:mainpage')
    else:
        f = PartyForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Party, pk=id, uid=uid)
                cd['pk'] = id
            p = Party(uid=User(uid), **cd)
            p.party_opt = text_opts_keys.index(cd['party_opt'])
            p.save()
            return redirect('sur:mainpage')
        else:
            err_message = inerr
    return render(
        request,
        'sur_partyform.html',
        {'app': APP,
         'f': f,
         'min_chars': grammar(MIN_LENGTH, GR_C),
         'page_title': page_title,
         'err_message': err_message})

@require_http_methods(['GET', 'POST'])
@login_required
def partydel(request, id=0):
    uid = request.user.id
    if request.method == 'GET':
        return render(
            request,
            'sur_partydel.html',
            {'app': APP,
             'page_title': 'Smazání účastníka'})
    else:
        if (getbutton(request) == 'yes'):
            get_object_or_404(Party, pk=id, uid=uid).delete()
            return redirect('sur:partydeleted')
        return redirect('sur:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):
    err_message = ''
    uid = request.user.id
    page_title = 'Sledování účastníků řízení'
    btn = getbutton(request)
    if request.method == 'GET':
        f = EmailForm(initial=model_to_dict(get_object_or_404(User, pk=uid)))
    else:
        f = EmailForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            p = get_object_or_404(User, pk=uid)
            p.email = cd['email']
            p.save()
            return redirect('sur:mainpage')
        else:
            err_message = inerr
    rows = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'id') \
        .values()
    for row in rows:
        row['party_opt_text'] = text_opts[row['party_opt']][1]
    return render(
        request,
        'sur_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows})
