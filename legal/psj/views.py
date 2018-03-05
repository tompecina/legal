# -*- coding: utf-8 -*-
#
# psj/views.py
#
# Copyright (C) 2011-18 Tomáš Pecina <tomas@pecina.cz>
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

from django.shortcuts import redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.gzip import gzip_page
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404

from legal.common.glob import REGISTERS, INERR, TEXT_OPTS_KEYS, ODP, EXLIM_TITLE, LOCAL_SUBDOMAIN, LOCAL_URL, DTF
from legal.common.utils import Pager, new_xml, xml_decorate, composeref, xmlbool, LOGGER, render
from legal.psj.models import Hearing
from legal.psj.forms import MainForm


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

EXLIM = 1000


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    err_message = ''
    page_title = apps.get_app_config(APP).verbose_name

    if request.method == 'GET':
        form = MainForm()
        return render(
            request,
            'psj_mainpage.xhtml',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'form': form})
    else:
        form = MainForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if not cld['party']:
                del cld['party_opt']
            query = QueryDict(mutable=True)
            for key in cld:
                if cld[key]:
                    query[key] = cld[key]
            query['start'] = 0
            del query['format']
            return redirect('{}?{}'.format(
                reverse('{}:{}list'.format(APP, cld['format'])),
                query.urlencode()))
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
            return render(
                request,
                'psj_mainpage.xhtml',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'form': form})


def g2p(reqd):

    par = {}

    lims = {
        'senate': 0,
        'number': 1,
        'year': 1,
        'courtroom': 1,
        'judge': 1,
    }
    for fld in lims:
        if fld in reqd:
            par[fld] = npar = int(reqd[fld])
            assert npar >= lims[fld]

    if 'court' in reqd:
        par['courtroom__court_id'] = reqd['court']
    if 'register' in reqd:
        assert reqd['register'] in REGISTERS
        par['register'] = reqd['register']
    if 'date_from' in reqd:
        par['time__gte'] = datetime.strptime(reqd['date_from'], DTF).date()
    if 'date_to' in reqd:
        par['time__lt'] = datetime.strptime(reqd['date_to'], DTF).date() + ODP
    if 'party_opt' in reqd:
        assert reqd['party_opt'] in TEXT_OPTS_KEYS
    if 'party' in reqd:
        assert 'party_opt' in reqd
        par['parties__name__' + reqd['party_opt']] = reqd['party']
    return par


@require_http_methods(('GET',))
def htmllist(request):

    LOGGER.debug('HTML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        start = int(reqd['start']) if 'start' in reqd else 0
        assert start >= 0
        res = Hearing.objects.filter(**par).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = res.count()
    if total and start >= total:
        start = total - 1
    return render(
        request,
        'psj_list.xhtml',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': res[start:start + BATCH],
         'pager': Pager(start, total, reverse('psj:htmllist'), reqd, BATCH),
         'today': date.today(),
         'total': total})


@gzip_page
@require_http_methods(('GET',))
def xmllist(request):

    LOGGER.debug('XML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Hearing.objects.filter(**par).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = res.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('psj:mainpage')})
    dec = {
        'hearings': {
            'xmlns': 'http://' + LOCAL_SUBDOMAIN,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'
            .format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = new_xml('')
    tag_hearings = xml_decorate(xml.new_tag('hearings'), dec)
    xml.append(tag_hearings)
    for item in res:
        tag_hearing = xml.new_tag('hearing')
        tag_hearings.append(tag_hearing)
        tag_court = xml.new_tag('court')
        tag_hearing.append(tag_court)
        tag_court['id'] = item.courtroom.court_id
        tag_court.append(item.courtroom.court.name)
        tag_courtroom = xml.new_tag('courtroom')
        tag_hearing.append(tag_courtroom)
        tag_courtroom.append(item.courtroom.desc)
        tag_time = xml.new_tag('time')
        tag_hearing.append(tag_time)
        tag_time.append(item.time.replace(microsecond=0).isoformat())
        tag_ref = xml.new_tag('ref')
        tag_hearing.append(tag_ref)
        tag_senate = xml.new_tag('senate')
        tag_senate.append(str(item.senate))
        tag_ref.append(tag_senate)
        tag_register = xml.new_tag('register')
        tag_register.append(item.register)
        tag_ref.append(tag_register)
        tag_number = xml.new_tag('number')
        tag_number.append(str(item.number))
        tag_ref.append(tag_number)
        tag_year = xml.new_tag('year')
        tag_year.append(str(item.year))
        tag_ref.append(tag_year)
        tag_judge = xml.new_tag('judge')
        tag_hearing.append(tag_judge)
        tag_judge.append(item.judge.name)
        tag_parties = xml.new_tag('parties')
        tag_hearing.append(tag_parties)
        for party in item.parties.values():
            tag_party = xml.new_tag('party')
            tag_parties.append(tag_party)
            tag_party.append(party['name'])
        tag_form = xml.new_tag('form')
        tag_hearing.append(tag_form)
        tag_form.append(item.form.name)
        tag_closed = xml.new_tag('closed')
        tag_hearing.append(tag_closed)
        tag_closed.append(xmlbool(item.closed))
        tag_cancelled = xml.new_tag('cancelled')
        tag_hearing.append(tag_cancelled)
        tag_cancelled.append(xmlbool(item.cancelled))
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Jednani.xml'
    return response


@gzip_page
@require_http_methods(('GET',))
def csvlist(request):

    LOGGER.debug('CSV list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Hearing.objects.filter(**par).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = res.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('psj:mainpage')})
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Jednani.csv'
    writer = csvwriter(response)
    hdr = (
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
    )
    writer.writerow(hdr)
    for item in res:
        dat = (
            item.courtroom.court.name,
            item.courtroom.desc,
            '{:%d.%m.%Y}'.format(item.time),
            '{:%H:%M}'.format(item.time),
            composeref(item.senate, item.register, item.number, item.year),
            item.judge.name,
            ';'.join([p['name'] for p in item.parties.values()]),
            item.form.name,
            'ano' if item.closed else 'ne',
            'ano' if item.cancelled else 'ne',
        )
        writer.writerow(dat)
    return response


@gzip_page
@require_http_methods(('GET',))
def jsonlist(request):

    LOGGER.debug('JSON list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Hearing.objects.filter(**par).order_by('time', 'pk').distinct()
    except:
        raise Http404
    total = res.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('psj:mainpage')})
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Jednani.json'
    lst = []
    for item in res:
        court = {
            'id': item.courtroom.court.id,
            'name': item.courtroom.court.name,
        }
        lst.append({
            'court': court,
            'courtroom': item.courtroom.desc,
            'time': item.time.isoformat(),
            'ref': {
                'senate': item.senate,
                'register': item.register,
                'number': item.number,
                'year': item.year,
            },
            'judge': item.judge.name,
            'parties': [p['name'] for p in item.parties.values()],
            'form': item.form.name,
            'closed': item.closed,
            'cancelled': item.cancelled,
        })
    dump(lst, response)
    return response


SJ_RE = compile(r'^(\S*\.\S*\s)*(.*)$')


def stripjudge(name):

    return strxfrm(SJ_RE.match(name['judge__name']).group(2))


@require_http_methods(('GET',))
def courtinfo(request, court):

    LOGGER.debug('Court information accessed, court="{}"'.format(court), request)
    courtrooms = (
        Hearing.objects.filter(courtroom__court_id=court).values('courtroom_id', 'courtroom__desc').distinct()
        .order_by('courtroom__desc'))
    judges = list(Hearing.objects.filter(courtroom__court_id=court).values('judge_id', 'judge__name').distinct())
    judges.sort(key=stripjudge)
    return render(
        request,
        'psj_court.xhtml',
        {'courtrooms': courtrooms,
         'judges': judges},
        content_type='text/plain; charset=utf-8')
