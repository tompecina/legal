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

from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404
from datetime import date, datetime
from math import floor, ceil
import csv
from common.utils import (
    formam, p2c, Pager, newXML, xmldecorate, composeref, xmlbool)
from common.glob import registers, inerr, text_opts, odp
from cnb.main import getFXrate
from szr.glob import supreme_court, supreme_administrative_court
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
        courts = Court.objects.exclude(id=supreme_court) \
            .exclude(id=supreme_administrative_court).order_by('name')
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
            return redirect(reverse('psj:' + cd['format'] + 'list') + \
                '?' + q.urlencode())
        else:
            err_message = inerr
            return render(
                request,
                'psj_mainpage.html',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'f': f})
def g2p(rd):
    p = {}
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
        p['time__gte'] = datetime.strptime(rd['date_from'], DTF).date()
    if 'date_to' in rd:
        p['time__lt'] = datetime.strptime(rd['date_to'], DTF).date() + odp
    if 'party_opt' in rd:
        assert rd['party_opt'] in dict(text_opts).keys()
    if 'party' in rd:
        assert 'party_opt' in rd
        p['parties__name__' + rd['party_opt']] = rd['party']
    return p
        
@require_http_methods(['GET'])
def htmllist(request):
    page_title = apps.get_app_config(APP).verbose_name
    rd = request.GET.copy()
    try:
        p = g2p(rd)
        start = int(rd['start']) if ('start' in rd) else 0
        assert start >= 0
    except:
        raise Http404
    d = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    total = len(d)
    if (start >= total) and (total > 0):
        start = total - 1
    return render(
        request,
        'psj_list.html',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': d[start:(start + BATCH)],
         'pager': Pager(start, total, reverse('psj:htmllist'), rd, BATCH),
         'today': date.today(),
         'total': total})

@require_http_methods(['GET'])
def xmllist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    hh = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    xd = {
        'hearings': {
            'xmlns': 'http://legal.pecina.cz',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://legal.pecina.cz ' \
            'https://legal.pecina.cz/static/%s-%s.xsd' % (APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = newXML('')
    tag_hearings = xmldecorate(xml.new_tag('hearings'), xd)
    xml.append(tag_hearings)
    for h in hh:
        tag_hearing = xml.new_tag('hearing')
        tag_hearings.append(tag_hearing)
        tag_court = xml.new_tag('court')
        tag_hearing.append(tag_court)
        tag_court['id'] = h.courtroom.court_id
        tag_court.append(h.courtroom.court.name)
        tag_courtroom = xml.new_tag('courtroom')
        tag_hearing.append(tag_courtroom)
        tag_courtroom.append(h.courtroom.desc)
        tag_time = xml.new_tag('time')
        tag_hearing.append(tag_time)
        tag_time.append(h.time.replace(microsecond=0).isoformat())
        tag_ref = xml.new_tag('ref')
        tag_hearing.append(tag_ref)
        tag_ref.append(composeref(h.senate, h.register, h.number, h.year))
        tag_judge = xml.new_tag('judge')
        tag_hearing.append(tag_judge)
        tag_judge.append(h.judge.name)
        tag_parties = xml.new_tag('parties')
        tag_hearing.append(tag_parties)
        for party in h.parties.values():
            tag_party = xml.new_tag('party')
            tag_parties.append(tag_party)
            tag_party.append(party['name'])
        tag_form = xml.new_tag('form')
        tag_hearing.append(tag_form)
        tag_form.append(h.form.name)
        tag_closed = xml.new_tag('closed')
        tag_hearing.append(tag_closed)
        tag_closed.append(xmlbool(h.closed))
        tag_cancelled = xml.new_tag('cancelled')
        tag_hearing.append(tag_cancelled)
        tag_cancelled.append(xmlbool(h.cancelled))
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n', content_type='text/xml')
    response['Content-Disposition'] = \
                'attachment; filename=Jednani.xml'
    return response

@require_http_methods(['GET'])
def csvlist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    hh = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename=Jednani.csv'
    writer = csv.writer(response)
    hdr = ['Soud',
           'Jednací síň',
           'Datum',
           'Čas',
           'Spisová značka',
           'Řešitel',
           'Účastníci řízení',
           'Druh jednání',
           'Neveřejné',
           'Zrušeno',
    ]
    writer.writerow(hdr)
    for h in hh:
        dat = [
            h.courtroom.court.name,
            h.courtroom.desc,
            h.time.strftime('%d.%m.%Y'),
            h.time.strftime('%H:%M'),
            composeref(h.senate, h.register, h.number, h.year),
            h.judge.name,
            ';'.join([p['name'] for p in h.parties.values()]),
            h.form.name,
            'ano' if h.closed else 'ne',
            'ano' if h.cancelled else 'ne',
        ]
        writer.writerow(dat)
    return response

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
