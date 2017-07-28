# -*- coding: utf-8 -*-
#
# psj/views.py
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

from datetime import date, datetime
from csv import writer as csvwriter
from json import dump
from re import compile
from locale import strxfrm
from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404
from common.utils import (
    Pager, newXML, xmldecorate, composeref, xmlbool, logger)
from common.glob import (
    registers, inerr, text_opts_keys, odp, exlim_title,
    localsubdomain, localurl, DTF)
from szr.glob import supreme_court, supreme_administrative_court
from szr.models import Court
from psj.models import Hearing
from psj.forms import MainForm


APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

EXLIM = 1000


@require_http_methods(['GET', 'POST'])
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    err_message = ''
    messages = []
    page_title = apps.get_app_config(APP).verbose_name

    courts = Court.objects.exclude(id=supreme_court) \
        .exclude(id=supreme_administrative_court).order_by('name')
    if request.method == 'GET':
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
            del q['format']
            return redirect('{}?{}'.format(
                reverse('{}:{}list'.format(APP, cd['format'])),
                q.urlencode()))
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
            return render(
                request,
                'psj_mainpage.html',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'courts': courts,
                 'f': f})


def g2p(rd):

    p = {}
    for f, l in [['senate', 0], ['number', 1], ['year', 1],
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
        assert rd['party_opt'] in text_opts_keys
    if 'party' in rd:
        assert 'party_opt' in rd
        p['parties__name__' + rd['party_opt']] = rd['party']
    return p


@require_http_methods(['GET'])
def htmllist(request):

    logger.debug('HTML list accessed', request, request.GET)
    page_title = apps.get_app_config(APP).verbose_name
    rd = request.GET.copy()
    try:
        p = g2p(rd)
        start = int(rd['start']) if ('start' in rd) else 0
        assert start >= 0
        d = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = d.count()
    if total and start >= total:
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

    logger.debug('XML list accessed', request, request.GET)
    rd = request.GET.copy()
    try:
        p = g2p(rd)
        hh = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = hh.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('psj:mainpage')})
    xd = {
        'hearings': {
            'xmlns': 'http://' + localsubdomain,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'
                .format(localsubdomain, localurl, APP, APPVERSION),
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
        tag_senate = xml.new_tag('senate')
        tag_senate.append(str(h.senate))
        tag_ref.append(tag_senate)
        tag_register = xml.new_tag('register')
        tag_register.append(h.register)
        tag_ref.append(tag_register)
        tag_number = xml.new_tag('number')
        tag_number.append(str(h.number))
        tag_ref.append(tag_number)
        tag_year = xml.new_tag('year')
        tag_year.append(str(h.year))
        tag_ref.append(tag_year)
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
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = \
                'attachment; filename=Jednani.xml'
    return response


@require_http_methods(['GET'])
def csvlist(request):

    logger.debug('CSV list accessed', request, request.GET)
    rd = request.GET.copy()
    try:
        p = g2p(rd)
        hh = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = hh.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('psj:mainpage')})
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=Jednani.csv'
    writer = csvwriter(response)
    hdr = [
        'Soud',
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
            '{:%d.%m.%Y}'.format(h.time),
            '{:%H:%M}'.format(h.time),
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
def jsonlist(request):

    logger.debug('JSON list accessed', request, request.GET)
    rd = request.GET.copy()
    try:
        p = g2p(rd)
        hh = Hearing.objects.filter(**p).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = hh.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('psj:mainpage')})
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=Jednani.json'
    r = []
    for h in hh:
        court = {
            'id': h.courtroom.court.id,
            'name': h.courtroom.court.name,
        }
        r.append({
            'court': court,
            'courtroom': h.courtroom.desc,
            'time': h.time.isoformat(),
            'ref': {
                'senate': h.senate,
                'register': h.register,
                'number': h.number,
                'year': h.year,
            },
            'judge': h.judge.name,
            'parties': [p['name'] for p in h.parties.values()],
            'form': h.form.name,
            'closed': h.closed,
            'cancelled': h.cancelled,
        })
    dump(r, response)
    return response


sjre = compile(r'^(\S*\.\S*\s)*(.*)$')


def stripjudge(name):

    return strxfrm(sjre.match(name['judge__name']).group(2))


@require_http_methods(['GET'])
def courtinfo(request, court):

    logger.debug(
        'Court information accessed, court="{}"'.format(court),
        request)
    courtrooms = Hearing.objects.filter(courtroom__court_id=court) \
        .values('courtroom_id', 'courtroom__desc').distinct() \
        .order_by('courtroom__desc')
    judges = list(Hearing.objects.filter(courtroom__court_id=court) \
        .values('judge_id', 'judge__name').distinct())
    judges.sort(key=stripjudge)
    return render(
        request,
        'psj_court.html',
        {'courtrooms': courtrooms,
         'judges': judges})
