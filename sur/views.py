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

from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.urls import reverse
from csv import reader as csvreader, writer as csvwriter
from io import StringIO
from common.utils import getbutton, grammar, between, Pager
from common.glob import (
    inerr, GR_C, text_opts, text_opts_keys, text_opts_abbr, text_opts_ca,
    text_opts_ai)
from szr.forms import EmailForm
from .forms import PartyForm, PartyBatchForm
from .models import Party
from .glob import MIN_LENGTH, MAX_LENGTH

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

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
            p = Party(uid_id=uid, **cd)
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
def partybatchform(request):

    err_message = ''
    uid = request.user.id

    if (request.method == 'GET'):
        f = PartyBatchForm()

    else:
        btn = getbutton(request)

        if btn == 'load':
            f = request.FILES.get('load')
            if not f:
                err_message = 'Nejprve zvolte soubor k načtení'
            else:
                try:
                    count = 0
                    with f:
                        for line in csvreader(StringIO(f.read().decode())):
                            line = line[0].strip()
                            if ':' in line:
                               line, party_opt = line.split(':', 1)
                            else:
                                party_opt = '*'
                            if between(MIN_LENGTH, len(line), MAX_LENGTH) and \
                                (party_opt in text_opts_abbr):
                                Party.objects.update_or_create(
                                    uid_id=uid,
                                    party=line,
                                    defaults={'party_opt': \
                                        text_opts_ai[party_opt]}
                                )
                                count += 1
                    return render(
                        request,
                        'sur_partybatchresult.html',
                        {'app': APP,
                         'page_title': 'Import účastníků řízení ze souboru',
                         'count': count})
                except:
                    err_message = 'Chyba při načtení souboru'

        f = PartyBatchForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            
            if (not btn) and cd['next']:
                return redirect(cd['next'])

        else:
            err_message = inerr

    return render(
        request,
        'sur_partybatchform.html',
        {'app': APP,
         'page_title': 'Import účastníků řízení ze souboru',
         'f': f,
         'err_message': err_message,
         'min_length': MIN_LENGTH,
         'max_length': MAX_LENGTH})

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):
    err_message = ''
    uid = request.user.id
    page_title = 'Sledování účastníků řízení'
    rd = request.GET.copy()
    start = int(rd['start']) if ('start' in rd) else 0
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
    p = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'pk') \
        .values()
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    for row in rows:
        row['party_opt_text'] = text_opts[row['party_opt']][1]
    return render(
        request,
        'sur_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sur:mainpage'), rd, BATCH),
         'total': total})

@require_http_methods(['GET'])
@login_required
def partyexport(request):
    uid = request.user.id
    pp = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'id') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=sur.csv'
    writer = csvwriter(response)
    for p in pp:
        dat = [p.party + text_opts_ca[p.party_opt]]
        writer.writerow(dat)
    return response
