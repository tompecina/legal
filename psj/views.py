# -*- coding: utf-8 -*-
#
# psj/views.py
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
from common.utils import formam, p2c, Pager
from common.glob import registers, inerr, text_opts
from cnb.main import getFXrate
from szr.models import Court
from .models import Hearing
from .forms import MainForm

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

DTF = '%Y-%m-%d'
        
@require_http_methods(['GET', 'POST'])
def mainpage(request):
    err_message = ''
    messages = []
    page_title = apps.get_app_config(APP).verbose_name

    if request.method == 'GET':
        courts = Court.objects.exclude(id='NSS').order_by('name')
        f = MainForm()
        return render(
            request,
            'psj_mainpage.html',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'courts': courts,
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
            q['start'] = 0
            return redirect(reverse('psj:list') + '?' + q.urlencode())
        else:
            err_message = inerr
            return render(
                request,
                'psj_mainpage.html',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'f': f})

@require_http_methods(['GET'])
def hearinglist(request):
    page_title = apps.get_app_config(APP).verbose_name
    rd = request.GET.copy()
    p = {}
    try:
        for f, l in [['senate', 0], ['number', 1], ['year', 1990],
                     ['courtroom', 1], ['judge', 1]]:
            if f in rd:
                p[f] = int(rd[f])
                assert p[f] >= l
        if 'court' in rd:
            p['courtroom__court_id'] = rd['court']
        if 'register' in rd:
            assert rd['register'] in registers
            p['register'] = rd['register']
        if 'date_from' in rd:
            p['date__gte'] = datetime.strptime(rd['date_from'], DTF).date()
        if 'date_to' in rd:
            p['date__lte'] = datetime.strptime(rd['date_to'], DTF).date()
        if 'party_opt' in rd:
            assert rd['party_opt'] in dict(text_opts).keys()
        if 'party' in rd:
            assert 'party_opt' in rd
            p['parties__name__' + rd['party_opt']] = rd['party']
        start = int(rd['start']) if ('start' in rd) else 0
        assert start >= 0
    except:
        raise Http404
    d = Hearing.objects.filter(**p).order_by('time', 'pk')
    total = len(d)
    if (start >= total) and (total > 0):
        start = total - 1
    return render(
        request,
        'psj_list.html',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': d[start:(start + BATCH)],
         'f': f,
         'pager': Pager(start, total, reverse('psj:list'), rd, BATCH),
         'total': total})

@require_http_methods(['GET'])
def courtinfo(request, court):
    courtrooms = Hearing.objects.filter(courtroom__court_id=court) \
        .values('courtroom_id', 'courtroom__desc').distinct() \
        .order_by('courtroom__desc')
    judges = Hearing.objects.filter(courtroom__court_id=court) \
        .values('judge_id', 'judge__name').distinct() \
        .order_by('judge__name')
    return render(
        request,
        'psj_court.html',
        {'courtrooms': courtrooms,
         'judges': judges})
