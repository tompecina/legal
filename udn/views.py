# -*- coding: utf-8 -*-
#
# udn/views.py
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

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404
from datetime import date, datetime
from math import floor, ceil
from common.utils import formam, p2c
from cnb.main import getFXrate
from szr.glob import registers
from .forms import MainForm, party_opts
from .models import Agenda, Decision, Party

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

DTF = '%Y-%m-%d'
        
def norm(x):
    return (x // BATCH) * BATCH

def gennav(
        start,
        total,
        prefix,
        suffix,
        i0='&lt;&lt;',
        i1='&lt;',
        i2='&gt;',
        i3='&gt;&gt;',
        a0='<span class="nav"><a href="',
        a1='">',
        a2='</a></span>',
        g0='<span class="nav grayed">',
        g1='</span>',
        s0='',
        s1='&nbsp;&nbsp;',
        s2='&nbsp;&nbsp;&nbsp;<span class="pager">',
        s2g='&nbsp;&nbsp;&nbsp;<span class="pager grayed">',
        s3='/',
        s4='</span>&nbsp;&nbsp;&nbsp;',
        s5='&nbsp;&nbsp;',
        s6=''):
    i = [i0, i1, i2, i3]
    n = [-1] * 4
    if start:
        n[0] = 0
        n[1] = start - BATCH
    if (start + BATCH) < total:
        n[2] = start + BATCH
        n[3] = norm(total - 1)
    p1 = (start // BATCH) + 1
    p2 = ((total - 1) // BATCH) + 1
    t = list(range(4))
    for j in range(4):
        if n[j] < 0:
            t[j] = g0 + i[j] + g1
        else:
            t[j] = a0 + prefix + str(n[j]) + suffix + a1 + i[j] + a2
    if p2 == 1:
        s2 = s2g
    return s0 + t[0] + s1 + t[1] + s2 + str(p1) + s3 + str(p2) + s4 + t[2] + \
        s5 + t[3] + s6

def listurl(d):
    return reverse('udn:list') + '?' + d.urlencode()

@require_http_methods(['GET', 'POST'])
def mainpage(request):
    err_message = ''
    messages = []
    page_title = apps.get_app_config(APP).verbose_name
    inerr = 'Chybné zadání, prosím, opravte údaje'

    if request.method == 'GET':
        agendas = Agenda.objects.all().order_by('desc')
        f = MainForm()
        return render(
            request,
            'udn_mainpage.html',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'agendas': agendas,
             'f': f})
    else:
        f = MainForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if not cd['party']:
                del cd['party_opt']
            q = QueryDict(mutable=True)
            for p in cd:
                if cd[p]:
                    q[p] = cd[p]
            return redirect(listurl(q))
        else:
            err_message = inerr
            return render(
                request,
                'udn_mainpage.html',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'f': f})

@require_http_methods(['GET'])
def declist(request):
    page_title = apps.get_app_config(APP).verbose_name
    rd = request.GET.copy()
    p = {}
    try:
        for f, l in [['senate', 0], ['number', 1], ['year', 1990],
                     ['page', 1], ['agenda', 1]]:
            if f in rd:
                p[f] = int(rd[f])
                assert p[f] >= l
        if 'register' in rd:
            assert rd['register'] in registers
            p['register'] = rd['register']
        if 'date_from' in rd:
            p['date__gte'] = datetime.strptime(rd['date_from'], DTF).date()
        if 'date_to' in rd:
            p['date__lte'] = datetime.strptime(rd['date_to'], DTF).date()
        if 'party_opt' in rd:
            assert rd['party_opt'] in dict(party_opts).keys()
        if 'party' in rd:
            assert 'party_opt' in rd
            p['parties__name__' + rd['party_opt']] = rd['party']
        start = int(rd['start']) if ('start' in rd) else 0
        assert start >= 0
        d = Decision.objects.filter(**p).order_by('-date', 'pk').distinct()
        total = len(d)
        if (start >= total) and (total > 0):
            start = total - 1
    except:
        raise Http404
    return render(
        request,
        'udn_list.html',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': d[start:(start + BATCH)],
         'f': f,
         'nav': gennav(start, total, listurl(rd) + '&start=', ''),
         'total': total})
