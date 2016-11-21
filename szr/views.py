# -*- coding: utf-8 -*-
#
# szr/views.py
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
from django.urls import reverse
from common.utils import getbutton, Pager
from common.glob import inerr
from .forms import EmailForm, ProcForm
from .models import Court, Proceedings
from .cron import addauxid, updateproc

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

@require_http_methods(['GET', 'POST'])
@login_required
def procform(request, id=0):
    err_message = ''
    uid = request.user.id
    page_title = ('Úprava řízení' if id else 'Nové řízení')
    btn = getbutton(request)
    courts = Court.objects.order_by('name')
    if request.method == 'GET':
        f = (ProcForm(initial=model_to_dict(get_object_or_404( \
            Proceedings, pk=id, uid=uid))) if id else ProcForm())
    elif btn == 'back':
        return redirect('szr:mainpage')
    else:
        f = ProcForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if not cd['senate']:
                cd['senate'] = '0'
            if id:
                p = get_object_or_404(Proceedings, pk=id, uid=uid)
                cd['pk'] = id
                cd['timestamp_add'] = p.timestamp_add
                cd['timestamp_update'] = p.timestamp_update
            cd['court_id'] = cd['court']
            del cd['court']
            onlydesc = ( \
                id and \
                p.court.id == cd['court_id'] and \
                p.senate == cd['senate'] and \
                p.register == cd['register'] and \
                p.number == cd['number'] and \
                p.year == cd['year'])
            if onlydesc:
                cd['changed'] = p.changed
                cd['updated'] = p.updated
                cd['hash'] = p.hash
                cd['auxid'] = p.auxid
                cd['notify'] = p.notify
            p = Proceedings(uid_id=uid, **cd)
            if not onlydesc:
                updateproc(p)
            p.save()
            return redirect('szr:mainpage')
        else:
            err_message = inerr
    return render(
        request,
        'szr_procform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'courts': courts})

@require_http_methods(['GET', 'POST'])
@login_required
def procdel(request, id=0):
    uid = request.user.id
    if request.method == 'GET':
        return render(
            request,
            'szr_procdel.html',
            {'app': APP,
             'page_title': 'Smazání řízení'})
    else:
        proc = get_object_or_404(Proceedings, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            proc.delete()
            return redirect('szr:procdeleted')
        return redirect('szr:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def procdelall(request):
    uid = request.user.id
    if request.method == 'GET':
        return render(
            request,
            'szr_procdelall.html',
            {'app': APP,
             'page_title': 'Smazání všech řízení'})
    else:
        if (getbutton(request) == 'yes') and \
           ('conf' in request.POST) and \
           (request.POST['conf'] == 'Ano'):
            Proceedings.objects.filter(uid=uid).delete()
        return redirect('szr:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):
    err_message = ''
    uid = request.user.id
    page_title = 'Sledování změn v řízení'
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
            return redirect('szr:mainpage')
        else:
            err_message = inerr
    p = Proceedings.objects.filter(uid=uid).order_by('desc', 'pk')
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    return render(
        request,
        'szr_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('szr:mainpage'), rd, BATCH),
         'total': total})
