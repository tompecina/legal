# -*- coding: utf-8 -*-
#
# szr/views.py
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

from datetime import date
from csv import reader as csvreader, writer as csvwriter
from io import StringIO

from django.shortcuts import get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.urls import reverse

from legal.common.glob import REGISTERS, NULL_REGISTERS, INERR
from legal.common.utils import getbutton, Pager, composeref, decomposeref, LOGGER, render
from legal.szr.forms import EmailForm, ProcForm
from legal.szr.models import Court, Proceedings
from legal.szr.cron import updateproc, p2s


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

BATCH = 50


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    err_message = ''
    uid = request.user.id
    page_title = 'Sledování změn v řízení'

    reqd = request.GET.copy()
    start = int(reqd['start']) if 'start' in reqd else 0
    if request.method == 'GET':
        form = EmailForm(initial=model_to_dict(get_object_or_404(User, pk=uid)))
    else:
        form = EmailForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            user = get_object_or_404(User, pk=uid)
            user.email = cld['email']
            user.save()
            return redirect('szr:mainpage')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    proc = Proceedings.objects.filter(uid=uid).order_by('desc', 'pk')
    total = proc.count()
    if start >= total and total:
        start = total - 1
    rows = proc[start:start + BATCH]
    return render(
        request,
        'szr_mainpage.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('szr:mainpage'), reqd, BATCH),
         'total': total,
         'NULL_REGISTERS': NULL_REGISTERS})


@require_http_methods(('GET', 'POST'))
@login_required
def procform(request, idx=0):

    LOGGER.debug('Proceedings form accessed using method {}, id={}'.format(request.method, idx), request, request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava řízení' if idx else 'Nové řízení'
    button = getbutton(request)
    if request.method == 'GET':
        form = ProcForm(initial=model_to_dict(get_object_or_404(Proceedings, pk=idx, uid=uid))) if idx else ProcForm()
    elif button == 'back':
        return redirect('szr:mainpage')
    else:
        form = ProcForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if not cld['senate']:
                cld['senate'] = 0
            if idx:
                proc = get_object_or_404(Proceedings, pk=idx, uid=uid)
                cld['pk'] = idx
                cld['timestamp_add'] = proc.timestamp_add
            cld['court_id'] = cld['court']
            del cld['court']
            onlydesc = (
                idx and proc.court.id == cld['court_id'] and proc.senate == cld['senate']
                and proc.register == cld['register'] and proc.number == cld['number'] and proc.year == cld['year'])
            if onlydesc:
                cld['changed'] = proc.changed
                cld['updated'] = proc.updated
                cld['hash'] = proc.hash
                cld['auxid'] = proc.auxid
                cld['notify'] = proc.notify
            proc = Proceedings(uid_id=uid, **cld)
            if not onlydesc:
                updateproc(proc)
            proc.save()
            LOGGER.info(
                'User "{}" ({:d}) {} proceedings "{}" ({})'
                .format(uname, uid, 'updated' if idx else 'added', proc.desc, p2s(proc)),
                request)
            return redirect('szr:mainpage')
        else:  # pragma: no cover
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    return render(
        request,
        'szr_procform.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def procdel(request, idx=0):

    LOGGER.debug(
        'Proceedings delete page accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    proc = get_object_or_404(Proceedings, pk=idx, uid=uid)
    if request.method == 'GET':
        return render(
            request,
            'szr_procdel.xhtml',
            {'app': APP,
             'page_title': 'Smazání řízení',
             'desc': proc.desc})
    else:
        if getbutton(request) == 'yes':
            LOGGER.info(
                'User "{}" ({:d}) deleted proceedings "{}" ({})'.format(uname, uid, proc.desc, p2s(proc)),
                request)
            proc.delete()
            return redirect('szr:procdeleted')
        return redirect('szr:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def procdelall(request):

    LOGGER.debug('Delete all proceedings page accessed using method {}'.format(request.method), request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'szr_procdelall.xhtml',
            {'app': APP,
             'page_title': 'Smazání všech řízení'})
    else:
        if getbutton(request) == 'yes' and 'conf' in request.POST and request.POST['conf'] == 'Ano':
            Proceedings.objects.filter(uid=uid).delete()
            LOGGER.info('User "{}" ({:d}) deleted all proceedings'.format(uname, uid), request)
        return redirect('szr:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def procbatchform(request):

    LOGGER.debug('Proceedings import page accessed using method {}'.format(request.method), request)

    err_message = ''
    uid = request.user.id
    uname = request.user.username
    today = date.today()

    if request.method == 'POST':
        button = getbutton(request)

        if button == 'load':
            infile = request.FILES.get('load')
            if not infile:
                err_message = 'Nejprve zvolte soubor k načtení'
            else:
                errors = []
                try:
                    count = 0
                    with infile:
                        idx = 0
                        for line in csvreader(StringIO(infile.read().decode())):
                            idx += 1
                            errlen = len(errors)
                            if not line:
                                continue
                            if len(line) != 3:
                                errors.append((idx, 'Chybný formát'))
                                continue
                            desc = line[0].strip()
                            if not desc:
                                errors.append((idx, 'Prázdný popis'))
                                continue
                            if len(desc) > 255:
                                errors.append((idx, 'Příliš dlouhý popis'))
                                continue
                            try:
                                court = line[1]
                                assert Court.objects.get(id=court)
                            except:
                                errors.append((idx, 'Chybná zkratka soudu'))
                                continue
                            try:
                                senate, register, number, year = decomposeref(line[2])
                                assert senate >= 0
                                assert register in REGISTERS
                                assert number > 0
                                assert year >= 1990 and year <= today.year
                            except:
                                errors.append((idx, 'Chybná spisová značka'))
                                continue
                            if len(errors) == errlen:
                                proc = Proceedings.objects.filter(
                                    uid_id=uid,
                                    desc=desc,
                                    court=court,
                                    senate=senate,
                                    register=register,
                                    number=number,
                                    year=year)
                                if not proc.exists():
                                    try:
                                        proc = Proceedings.objects.update_or_create(
                                                uid_id=uid,
                                                desc=desc,
                                                defaults={
                                                    'court_id': court,
                                                    'senate': senate,
                                                    'register': register,
                                                    'number': number,
                                                    'year': year,
                                                    'changed': None,
                                                    'updated': None,
                                                    'hash': '',
                                                    'auxid': 0,
                                                    'notify': False})[0]
                                        updateproc(proc)
                                        proc.save()
                                    except:
                                        errors.append((idx, 'Popisu "{}" odpovídá více než jedno řízení'.format(desc)))
                                        continue
                                count += 1
                    LOGGER.info('User "{}" ({:d}) imported {:d} proceedings'.format(uname, uid, count), request)
                    return render(
                        request,
                        'szr_procbatchresult.xhtml',
                        {'app': APP,
                         'page_title': 'Import řízení ze souboru',
                         'count': count,
                         'errors': errors})

                except:  # pragma: no cover
                    LOGGER.error('Error reading file', request)
                    err_message = 'Chyba při načtení souboru'

    return render(
        request,
        'szr_procbatchform.xhtml',
        {'app': APP,
         'page_title': 'Import řízení ze souboru',
         'err_message': err_message})


@require_http_methods(('GET',))
@login_required
def procexport(request):

    LOGGER.debug('Proceedings export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    res = Proceedings.objects.filter(uid=uid).order_by('desc', 'pk').distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=szr.csv'
    writer = csvwriter(response)
    for proc in res:
        dat = (
            proc.desc,
            proc.court.id,
            composeref(
                proc.senate,
                proc.register,
                proc.number,
                proc.year)
        )
        writer.writerow(dat)
    LOGGER.info('User "{}" ({:d}) exported proceedings'.format(uname, uid), request)
    return response


@require_http_methods(('GET',))
def courts(request):

    LOGGER.debug('List of courts accessed', request)
    return render(
        request,
        'szr_courts.xhtml',
        {'app': APP,
         'page_title': 'Přehled soudů',
         'rows': Court.objects.order_by('name').values('id', 'name')})
