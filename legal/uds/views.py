# -*- coding: utf-8 -*-
#
# uds/views.py
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

from legal.common.glob import (
    INERR, TEXT_OPTS_KEYS, REPO_URL, EXLIM_TITLE, FTLIM_TITLE, LOCAL_SUBDOMAIN, LOCAL_URL, DTF, ODP)
from legal.common.utils import Pager, new_xml, xml_decorate, LOGGER, render

from legal.uds.forms import MainForm
from legal.uds.models import Agenda, Document, DocumentIndex, File

APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

REPO_PREFIX = join(REPO_URL, APP)

EXLIM = 1000
FTLIM = 1000
assert FTLIM <= EXLIM


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
            'uds_mainpage.xhtml',
            {'app': APP,
             'page_title': page_title,
             'err_message': err_message,
             'agendas': agendas,
             'form': form})
    form = MainForm(request.POST)
    if form.is_valid():
        cld = form.cleaned_data
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
        'uds_mainpage.xhtml',
        {'app': APP,
         'page_title': page_title,
         'err_message': err_message,
         'agendas': agendas,
         'form': form})


def g2p(reqd):

    par = {}
    if 'publisher' in reqd:
        par['publisher_id'] = reqd['publisher']

    lims = {
        'senate': 0,
        'number': 1,
        'year': 1970,
        'page': 1,
        'agenda': 1,
    }
    for fld in lims:
        if fld in reqd:
            par[fld] = npar = int(reqd[fld])
            assert npar >= lims[fld]

    if 'register' in reqd:
        par['register'] = reqd['register'].upper()
    if 'date_posted_from' in reqd:
        par['posted__gte'] = datetime.strptime(reqd['date_posted_from'], DTF).date()
    if 'date_posted_to' in reqd:
        par['posted__lt'] = datetime.strptime(reqd['date_posted_to'], DTF).date() + ODP
    if 'text' in reqd:
        par['text__search'] = reqd['text']

    return par


@require_http_methods(('GET',))
def htmllist(request):

    LOGGER.debug('HTML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        start = int(reqd['start']) if 'start' in reqd else 0
        assert start >= 0
        docins = DocumentIndex.objects.using('sphinx').filter(**par).order_by('-posted', 'id')
        total = docins.count()
        if total and start >= total:
            start = total - 1
        if start >= FTLIM:
            if 'text' in reqd:
                return render(
                    request,
                    'ftlim.xhtml',
                    {'app': APP,
                     'page_title': FTLIM_TITLE,
                     'limit': FTLIM,
                     'back': reverse('uds:mainpage')})
            docs = Document.objects.filter(**par).order_by('-posted', 'id').distinct()
            total = docs.count()
            if total and start >= total:
                start = total - 1
            docs = docs[start:(start + BATCH)]
        else:
            docins = list(docins[start:(start + BATCH)].values_list('id', flat=True))
            docs = Document.objects.filter(id__in=docins).order_by('-posted', 'id').distinct()
        for doc in docs:
            doc.files = File.objects.filter(document=doc).order_by('fileid').distinct()
            idx = 1
            for file in doc.files:
                file.brk = idx % 5 == 0
                idx += 1
    except:
        raise Http404
    return render(
        request,
        'uds_list.xhtml',
        {'app': APP,
         'page_title': 'Výsledky vyhledávání',
         'rows': docs,
         'pager': Pager(start, total, reverse('uds:htmllist'), reqd, BATCH),
         'total': total})


@gzip_page
@require_http_methods(('GET',))
def xmllist(request):

    LOGGER.debug('XML list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        resins = DocumentIndex.objects.using('sphinx').filter(**par).order_by('posted', 'id')
    except:
        raise Http404
    total = resins.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('uds:mainpage')})
    resins = list(resins.values_list('id', flat=True))
    res = Document.objects.filter(id__in=resins).order_by('posted', 'id').distinct()
    doc = {
        'documents': {
            'xmlns': 'http://' + LOCAL_SUBDOMAIN,
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://{} {}/static/{}-{}.xsd'.format(LOCAL_SUBDOMAIN, LOCAL_URL, APP, APPVERSION),
            'application': APP,
            'version': APPVERSION,
            'created': datetime.now().replace(microsecond=0).isoformat()
        }
    }
    xml = new_xml('')
    tag_documents = xml_decorate(xml.new_tag('documents'), doc)
    xml.append(tag_documents)
    for item in res:
        tag_document = xml.new_tag('document')
        tag_documents.append(tag_document)
        tag_document['id'] = item.docid
        tag_publisher = xml.new_tag('publisher')
        tag_document.append(tag_publisher)
        tag_publisher['id'] = item.publisher.pubid
        tag_publisher.append(item.publisher.name)
        tag_ref = xml.new_tag('ref')
        tag_document.append(tag_ref)
        tag_ref.append(item.ref)
        tag_description = xml.new_tag('description')
        tag_document.append(tag_description)
        tag_description.append(item.desc)
        tag_agenda = xml.new_tag('agenda')
        tag_document.append(tag_agenda)
        tag_agenda.append(item.agenda.desc)
        tag_posted = xml.new_tag('posted')
        tag_document.append(tag_posted)
        tag_posted.append(item.posted.isoformat())
        tag_files = xml.new_tag('files')
        tag_document.append(tag_files)
        for fil in File.objects.filter(document=item).order_by('fileid').distinct():
            tag_file = xml.new_tag('file')
            tag_files.append(tag_file)
            tag_file['id'] = fil.fileid
            tag_name = xml.new_tag('name')
            tag_file.append(tag_name)
            tag_name.append(fil.name)
            tag_url = xml.new_tag('url')
            tag_file.append(tag_url)
            tag_url.append(join(REPO_PREFIX, str(fil.fileid), fil.name))
    response = HttpResponse(
        str(xml).encode('utf-8') + b'\n',
        content_type='text/xml; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Dokumenty.xml'
    return response


@gzip_page
@require_http_methods(('GET',))
def csvlist(request):

    LOGGER.debug('CSV list accessed', request, request.GET)
    reqd = request.GET.copy()
    try:
        par = g2p(reqd)
        resins = DocumentIndex.objects.using('sphinx').filter(**par).order_by('posted', 'id')
    except:
        raise Http404
    total = resins.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('uds:mainpage')})
    resins = list(resins.values_list('id', flat=True))
    res = Document.objects.filter(id__in=resins).order_by('posted', 'id').distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Dokumenty.csv'
    writer = csvwriter(response)
    hdr = (
        'Datum vyvěšení',
        'Soud/státní zastupitelství',
        'Popis dokumentu',
        'Spisová značka/číslo jednací',
        'Agenda',
        'Soubory',
    )
    writer.writerow(hdr)
    for item in res:
        files = File.objects.filter(document=item).order_by('fileid').distinct()
        dat = (
            '{:%d.%m.%Y}'.format(item.posted),
            item.publisher.name,
            item.desc,
            item.ref,
            item.agenda.desc,
            ';'.join([join(REPO_PREFIX, str(fil.fileid), fil.name) for fil in files]),
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
        resins = DocumentIndex.objects.using('sphinx').filter(**par).order_by('posted', 'id')
    except:
        raise Http404
    total = resins.count()
    if total > EXLIM:
        return render(
            request,
            'exlim.xhtml',
            {'app': APP,
             'page_title': EXLIM_TITLE,
             'limit': EXLIM,
             'total': total,
             'back': reverse('uds:mainpage')})
    resins = list(resins.values_list('id', flat=True))
    res = Document.objects.filter(id__in=resins).order_by('posted', 'id').distinct()
    response = HttpResponse(content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=Dokumenty.json'
    lst = []
    for item in res:
        files = File.objects.filter(document=item).order_by('fileid').distinct()
        lst.append({
            'posted': item.posted.isoformat(),
            'publisher': item.publisher.name,
            'desc': item.desc,
            'ref': item.ref,
            'agenda': item.agenda.desc,
            'files': [{
                'id': f.fileid,
                'name': f.name,
                'url': join(REPO_PREFIX, str(f.fileid), f.name)}
                      for f in files],
        })
    dump(lst, response)
    return response
