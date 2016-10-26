# -*- coding: utf-8 -*-
#
# sir/views.py
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
from locale import strxfrm
from common.utils import getbutton, grammar, between, Pager
from common.glob import inerr, GR_C, text_opts, text_opts_keys
from szr.forms import EmailForm
from .glob import l2n, l2s
from .models import Vec, Insolvency
from .forms import InsForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

@require_http_methods(['GET', 'POST'])
@login_required
def insform(request, id=0):
    err_message = ''
    uid = request.user.id
    page_title = ('Úprava řízení' if id else 'Nové řízení')
    btn = getbutton(request)
    if request.method == 'GET':
        f = (InsForm(initial=model_to_dict(get_object_or_404( \
            Insolvency, pk=id, uid=uid))) if id else InsForm())
    elif btn == 'back':
        return redirect('sir:mainpage')
    else:
        f = InsForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Insolvency, pk=id, uid=uid)
                cd['pk'] = id
            p = Insolvency(uid_id=uid, **cd)
            p.save()
            return redirect('sir:mainpage')
        else:
            err_message = inerr
    return render(
        request,
        'sir_insform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message})

@require_http_methods(['GET', 'POST'])
@login_required
def insdel(request, id=0):
    uid = request.user.id
    if request.method == 'GET':
        return render(
            request,
            'sir_insdel.html',
            {'app': APP,
             'page_title': 'Smazání řízení'})
    else:
        if (getbutton(request) == 'yes'):
            get_object_or_404(Insolvency, pk=id, uid=uid).delete()
            return redirect('sir:insdeleted')
        return redirect('sir:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):
    err_message = ''
    uid = request.user.id
    page_title = 'Sledování změn v insolvenčních řízeních'
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
            return redirect('sir:mainpage')
        else:
            err_message = inerr
    p = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk')
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    return render(
        request,
        'sir_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sir:mainpage'), rd, BATCH),
         'total': total})

@require_http_methods(['GET'])
def courts(request):
    courts = sorted([{'short': l2s[x], 'name': l2n[x]} for x in \
        Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()], \
        key=(lambda x: strxfrm(x['name'])))
    return render(
        request,
        'sir_courts.html',
        {'page_title': 'Přehled insolvenčních soudů', 'rows': courts})
