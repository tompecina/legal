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

from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404
from datetime import date, datetime
from math import floor, ceil
from csv import writer as csvwriter
from json import dump
from common.utils import (
    formam, p2c, Pager, newXML, xmldecorate, composeref, xmlbool)
from common.glob import (
    registers, inerr, text_opts, text_opts_keys, repourl, exlim_title,
    localsubdomain, localurl, DTF)
from cnb.main import getFXrate
from szr.glob import (
    supreme_administrative_court, supreme_administrative_court_name)
from .forms import MainForm
from .models import Agenda, Decision, Party

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

repoprefix = repourl + APP + '/'

EXLIM = 1000

@require_http_methods(['GET', 'POST'])
def mainpage(request):
    err_message = ''
    messages = []
    page_title = apps.get_app_config(APP).verbose_name

    agendas = Agenda.objects.all().order_by('desc')
    if request.method == 'GET':
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
            q['start'] = 0
            del q['format']
            return redirect(reverse('udn:' + cd['format'] + 'list') + \
                '?' + q.urlencode())
        else:
            err_message = inerr
            return render(
                request,
                'udn_mainpage.html',
                {'app': APP,
                 'page_title': page_title,
                 'err_message': err_message,
                 'agendas': agendas,
                 'f': f})

def g2p(rd):
    p = {}
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
        assert rd['party_opt'] in text_opts_keys
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
    d = Decision.objects.filter(**p).order_by('-date', 'pk').distinct()
    total = d.count()
    if (start >= total) and (total > 0):
        start = total - 1
    return render(
        request,
        'udn_list.html',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': d[start:(start + BATCH)],
         'pager': Pager(start, total, reverse('udn:htmllist'), rd, BATCH),
         'total': total})

@require_http_methods(['GET'])
def xmllist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    dd = Decision.objects.filter(**p).order_by('date', 'pk').distinct()
    total = dd.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('udn:mainpage')})
    xd = {
        'decisions': {
            'xmlns': 'http://' + localsubdomain,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': ('http://' + localsubdomain + ' ' + \
            localurl + '/static/%s-%s.xsd') % (APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = newXML('')
    tag_decisions = xmldecorate(xml.new_tag('decisions'), xd)
    xml.append(tag_decisions)
    for d in dd:
        tag_decision = xml.new_tag('decision')
        tag_decisions.append(tag_decision)
        tag_court = xml.new_tag('court')
        tag_decision.append(tag_court)
        tag_court['id'] = supreme_administrative_court
        tag_court.append(supreme_administrative_court_name)
        tag_date = xml.new_tag('date')
        tag_decision.append(tag_date)
        tag_date.append(d.date.isoformat())
        tag_ref = xml.new_tag('ref')
        tag_decision.append(tag_ref)
        tag_senate = xml.new_tag('senate')
        tag_senate.append(str(d.senate))
        tag_ref.append(tag_senate)
        tag_register = xml.new_tag('register')
        tag_register.append(d.register)
        tag_ref.append(tag_register)
        tag_number = xml.new_tag('number')
        tag_number.append(str(d.number))
        tag_ref.append(tag_number)
        tag_year = xml.new_tag('year')
        tag_year.append(str(d.year))
        tag_ref.append(tag_year)
        tag_page = xml.new_tag('page')
        tag_page.append(str(d.page))
        tag_ref.append(tag_page)
        tag_agenda = xml.new_tag('agenda')
        tag_decision.append(tag_agenda)
        tag_agenda.append(d.agenda.desc)
        tag_parties = xml.new_tag('parties')
        tag_decision.append(tag_parties)
        for party in d.parties.values():
            tag_party = xml.new_tag('party')
            tag_parties.append(tag_party)
            tag_party.append(party['name'])
        tag_files = xml.new_tag('files')
        tag_decision.append(tag_files)
        tag_file = xml.new_tag('file')
        tag_files.append(tag_file)
        tag_file['type'] = 'abridged'
        tag_file.append(repoprefix + d.filename)
        if d.anonfilename:
            tag_file = xml.new_tag('file')
            tag_files.append(tag_file)
            tag_file['type'] = 'anonymized'
            tag_file.append(repoprefix + d.anonfilename)
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = \
                'attachment; filename=Rozhodnuti.xml'
    return response

@require_http_methods(['GET'])
def csvlist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    dd = Decision.objects.filter(**p).order_by('date', 'pk').distinct()
    total = dd.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('udn:mainpage')})
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=Rozhodnuti.csv'
    writer = csvwriter(response)
    hdr = [
        'Soud',
        'Datum',
        'Číslo jednací',
        'Oblast',
        'Účastníci řízení',
        'Zkrácené znění',
        'Anonymisované znění',
    ]
    writer.writerow(hdr)
    for d in dd:
        dat = [
            supreme_administrative_court_name,
            d.date.strftime('%d.%m.%Y'),
            composeref(d.senate, d.register, d.number, d.year, d.page),
            d.agenda.desc,
            ';'.join([p['name'] for p in d.parties.values()]),
            repoprefix + d.filename,
            (repoprefix + d.anonfilename) if d.anonfilename else '',
        ]
        writer.writerow(dat)
    return response

@require_http_methods(['GET'])
def jsonlist(request):
    rd = request.GET.copy()
    try:
        p = g2p(rd)
    except:
        raise Http404
    dd = Decision.objects.filter(**p).order_by('date', 'pk').distinct()
    total = dd.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.html',
            {'app': APP,
             'page_title': exlim_title,
             'limit': EXLIM,
             'total': total,
             'back': reverse('udn:mainpage')})
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=Rozhodnuti.json'
    r = []
    court = {
        'id': supreme_administrative_court,
        'name': supreme_administrative_court_name,
    }
    for d in dd:
        files = {'abridged': repoprefix + d.filename}
        if d.anonfilename:
            files['anonymized'] = repoprefix + d.anonfilename
        r.append({
            'court': court,
            'date': d.date.isoformat(),
            'ref': {
                'senate': d.senate,
                'register': d.register,
                'number': d.number,
                'year': d.year,
                'page': d.page,
            },
            'agenda': d.agenda.desc,
            'parties': [p['name'] for p in d.parties.values()],
            'files': files,
        })
    dump(r, response)
    return response
