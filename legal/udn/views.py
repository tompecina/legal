# -*- coding: utf-8 -*-
#
# udn/views.py
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

from datetime import datetime
from csv import writer as csvwriter
from json import dump
from os.path import join

from django.shortcuts import redirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.gzip import gzip_page
from django.apps import apps
from django.urls import reverse
from django.http import QueryDict, Http404

from legal.common.glob import REGISTERS, INERR, TEXT_OPTS_KEYS, REPO_URL, EXLIM_TITLE, LOCAL_SUBDOMAIN, LOCAL_URL, DTF
from legal.common.utils import Pager, new_xml, xml_decorate, composeref, LOGGER, render
from legal.szr.glob import SUPREME_ADMINISTRATIVE_COURT, SUPREME_ADMINISTRATIVE_COURT_NAME
from legal.udn.forms import MainForm
from legal.udn.models import Agenda, Decision


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

REPO_PREFIX = join(REPO_URL, APP)

EXLIM = 1000


@require_http_methods(('GET', 'POST'))
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    err_message = ''
    page_title = apps.get_app_config(APP).verbose_name

    agendas = Agenda.objects.all().order_by('desc')
    if request.method == 'GET':
        form = MainForm()
        return render(
            request,
            'udn_mainpage.xhtml',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'agendas': agendas,
             'form': form})
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
        return redirect('{}?{}'.format(reverse('{}:{}list'.format(APP, cld['format'])), query.urlencode()))
    err_message = INERR
    LOGGER.debug('Invalid form', request)
    return render(
        request,
        'udn_mainpage.xhtml',
        {'app': APP,
         'page_title': page_title,
         'err_message': err_message,
         'agendas': agendas,
         'form': form})


def g2p(reqd):

    par = {}

    lims = {
        'senate': 0,
        'number': 1,
        'year': 1990,
        'page': 1,
        'agenda': 1,
    }
    for fld in lims:
        if fld in reqd:
            par[fld] = npar = int(reqd[fld])
            assert npar >= lims[fld]

    if 'register' in reqd:
        assert reqd['register'] in REGISTERS
        par['register'] = reqd['register']
    if 'date_from' in reqd:
        par['date__gte'] = datetime.strptime(reqd['date_from'], DTF).date()
    if 'date_to' in reqd:
        par['date__lte'] = datetime.strptime(reqd['date_to'], DTF).date()
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
        dec = Decision.objects.filter(**par).order_by('-date', 'pk').distinct()
    except:
        raise Http404
    total = dec.count()
    if total and start >= total:
        start = total - 1
    return render(
        request,
        'udn_list.xhtml',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': dec[start:(start + BATCH)],
         'pager': Pager(start, total, reverse('udn:htmllist'), reqd, BATCH),
         'total': total})


@gzip_page
@require_http_methods(('GET',))
def xmllist(request):

    LOGGER.debug('XML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Decision.objects.filter(**par).order_by('date', 'pk').distinct()
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
             'back': reverse('udn:mainpage')})
    dec = {
        'decisions': {
            'xmlns': 'http://' + LOCAL_SUBDOMAIN,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'.format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = new_xml('')
    tag_decisions = xml_decorate(xml.new_tag('decisions'), dec)
    xml.append(tag_decisions)
    for item in res:
        tag_decision = xml.new_tag('decision')
        tag_decisions.append(tag_decision)
        tag_court = xml.new_tag('court')
        tag_decision.append(tag_court)
        tag_court['id'] = SUPREME_ADMINISTRATIVE_COURT
        tag_court.append(SUPREME_ADMINISTRATIVE_COURT_NAME)
        tag_date = xml.new_tag('date')
        tag_decision.append(tag_date)
        tag_date.append(item.date.isoformat())
        tag_ref = xml.new_tag('ref')
        tag_decision.append(tag_ref)
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
        tag_page = xml.new_tag('page')
        tag_page.append(str(item.page))
        tag_ref.append(tag_page)
        tag_agenda = xml.new_tag('agenda')
        tag_decision.append(tag_agenda)
        tag_agenda.append(item.agenda.desc)
        tag_parties = xml.new_tag('parties')
        tag_decision.append(tag_parties)
        for party in item.parties.values():
            tag_party = xml.new_tag('party')
            tag_parties.append(tag_party)
            tag_party.append(party['name'])
        tag_files = xml.new_tag('files')
        tag_decision.append(tag_files)
        tag_file = xml.new_tag('file')
        tag_files.append(tag_file)
        tag_file['type'] = 'abridged'
        tag_file.append(join(REPO_PREFIX, item.filename))
        if item.anonfilename:
            tag_file = xml.new_tag('file')
            tag_files.append(tag_file)
            tag_file['type'] = 'anonymized'
            tag_file.append(join(REPO_PREFIX, item.anonfilename))
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Rozhodnuti.xml'
    return response


@gzip_page
@require_http_methods(('GET',))
def csvlist(request):

    LOGGER.debug('CSV list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        res = Decision.objects.filter(**par).order_by('date', 'pk').distinct()
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
             'back': reverse('udn:mainpage')})
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Rozhodnuti.csv'
    writer = csvwriter(response)
    hdr = (
        'Soud',
        'Datum',
        'Číslo jednací',
        'Oblast',
        'Účastníci řízení',
        'Zkrácené znění',
        'Anonymisované znění',
    )
    writer.writerow(hdr)
    for item in res:
        dat = (
            SUPREME_ADMINISTRATIVE_COURT_NAME,
            '{:%d.%m.%Y}'.format(item.date),
            composeref(item.senate, item.register, item.number, item.year, item.page),
            item.agenda.desc,
            ';'.join([par['name'] for par in item.parties.values()]),
            join(REPO_PREFIX, item.filename),
            join(REPO_PREFIX, item.anonfilename) if item.anonfilename else '',
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
        res = Decision.objects.filter(**par).order_by('date', 'pk').distinct()
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
             'back': reverse('udn:mainpage')})
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Rozhodnuti.json'
    lst = []
    court = {
        'id': SUPREME_ADMINISTRATIVE_COURT,
        'name': SUPREME_ADMINISTRATIVE_COURT_NAME,
    }
    for item in res:
        files = {'abridged': join(REPO_PREFIX, item.filename)}
        if item.anonfilename:
            files['anonymized'] = join(REPO_PREFIX, item.anonfilename)
        lst.append({
            'court': court,
            'date': item.date.isoformat(),
            'ref': {
                'senate': item.senate,
                'register': item.register,
                'number': item.number,
                'year': item.year,
                'page': item.page,
            },
            'agenda': item.agenda.desc,
            'parties': [p['name'] for p in item.parties.values()],
            'files': files,
        })
    dump(lst, response)
    return response
