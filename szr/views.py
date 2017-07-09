# -*- coding: utf-8 -*-
#
# szr/views.py
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

from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.urls import reverse
from datetime import date
from csv import reader as csvreader, writer as csvwriter
from io import StringIO
from common.utils import getbutton, Pager, composeref, decomposeref, logger
from common.glob import registers, inerr
from .forms import EmailForm, ProcForm
from .models import Court, Proceedings
from .cron import addauxid, updateproc, p2s

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)

    err_message = ''
    uid = request.user.id
    page_title = 'Sledování změn v řízení'

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
            return redirect('szr:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    p = Proceedings.objects.filter(uid=uid).order_by('desc', 'pk')
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    return render(
        request,
        'szr_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('szr:mainpage'), rd, BATCH),
         'total': total})

@require_http_methods(['GET', 'POST'])
@login_required
def procform(request, id=0):
    logger.debug(
        'Proceedings form accessed using method {}, id={}' \
            .format(request.method, id),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = ('Úprava řízení' if id else 'Nové řízení')
    btn = getbutton(request)
    courts = Court.objects.order_by('name')
    if request.method == 'GET':
        f = (ProcForm(initial=model_to_dict(get_object_or_404( \
            Proceedings, pk=id, uid=uid))) if id else ProcForm())
    elif btn == 'back':
        return redirect('szr:mainpage')
    else:
        f = ProcForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if not cd['senate']:
                cd['senate'] = 0
            if id:
                p = get_object_or_404(Proceedings, pk=id, uid=uid)
                cd['pk'] = id
                cd['timestamp_add'] = p.timestamp_add
                cd['timestamp_update'] = p.timestamp_update
            cd['court_id'] = cd['court']
            del cd['court']
            onlydesc = ( \
                id and \
                p.court.id == cd['court_id'] and \
                p.senate == cd['senate'] and \
                p.register == cd['register'] and \
                p.number == cd['number'] and \
                p.year == cd['year'])
            if onlydesc:
                cd['changed'] = p.changed
                cd['updated'] = p.updated
                cd['hash'] = p.hash
                cd['auxid'] = p.auxid
                cd['notify'] = p.notify
            p = Proceedings(uid_id=uid, **cd)
            if not onlydesc:
                updateproc(p)
            p.save()
            if id:
                logger.info(
                    'User "{}" ({:d}) updated proceedings "{}" ({})' \
                        .format(uname, uid, p.desc, p2s(p)),
                    request)
            else:
                logger.info(
                    'User "{}" ({:d}) added proceedings "{}" ({})' \
                        .format(uname, uid, p.desc, p2s(p)),
                    request)
            return redirect('szr:mainpage')
        else:  # pragma: no cover
            logger.debug('Invalid form', request)
            err_message = inerr
    return render(
        request,
        'szr_procform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'courts': courts})

@require_http_methods(['GET', 'POST'])
@login_required
def procdel(request, id=0):
    logger.debug(
        'Proceedings delete page accessed using method {}, id={}' \
            .format(request.method, id),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'szr_procdel.html',
            {'app': APP,
             'page_title': 'Smazání řízení'})
    else:
        proc = get_object_or_404(Proceedings, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            logger.info(
                'User "{}" ({:d}) deleted proceedings "{}" ({})' \
                    .format(uname, uid, proc.desc, p2s(proc)),
                request)
            proc.delete()
            return redirect('szr:procdeleted')
        return redirect('szr:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def procdelall(request):
    logger.debug(
        'Delete all proceedings page accessed using method {}' \
            .format(request.method),
        request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'szr_procdelall.html',
            {'app': APP,
             'page_title': 'Smazání všech řízení'})
    else:
        if (getbutton(request) == 'yes') and \
           ('conf' in request.POST) and \
           (request.POST['conf'] == 'Ano'):
            Proceedings.objects.filter(uid=uid).delete()
            logger.info(
                'User "{}" ({:d}) deleted all proceedings'.format(uname, uid),
                request)
        return redirect('szr:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def procbatchform(request):

    logger.debug(
        'Proceedings import page accessed using method {}' \
            .format(request.method),
        request)

    err_message = ''
    uid = request.user.id
    uname = request.user.username
    today = date.today()

    if (request.method == 'POST'):
        btn = getbutton(request)

        if btn == 'load':
            f = request.FILES.get('load')
            if not f:
                err_message = 'Nejprve zvolte soubor k načtení'
            else:
                errors = []
                try:
                    count = 0
                    with f:
                        i = 0
                        for line in csvreader(StringIO(f.read().decode())):
                            i += 1
                            errlen = len(errors)
                            if not line:
                                continue
                            if len(line) != 3:
                                errors.append([i, 'Chybný formát'])
                                continue
                            desc = line[0].strip()
                            if not desc:
                                errors.append([i, 'Prázdný popis'])
                                continue
                            if len(desc) > 255:
                                errors.append([i, 'Příliš dlouhý popis'])
                                continue
                            try:
                                court = line[1]
                                assert Court.objects.get(id=court)
                            except:
                                errors.append([i, 'Chybná zkratka soudu'])
                                continue
                            try:
                                senate, register, number, year = \
                                    decomposeref(line[2])
                                assert senate >= 0
                                assert register in registers
                                assert number > 0
                                assert (year >= 1990) and (year <= today.year)
                            except:
                                errors.append([i, 'Chybná spisová značka'])
                                continue
                            if len(errors) == errlen:
                                p = Proceedings.objects.filter(
                                    uid_id=uid,
                                    desc=desc,
                                    court=court,
                                    senate=senate,
                                    register=register,
                                    number=number,
                                    year=year)
                                if not p.exists():
                                    try:
                                        p, pc = Proceedings.objects. \
                                            update_or_create(
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
                                                'notify': False})
                                        updateproc(p)
                                        p.save()
                                    except:
                                        errors.append(
                                            [i,
                                             'Popisu "{}" odpovídá více než ' \
                                             'jedno řízení'.format(desc)])
                                        continue
                                count += 1
                    logger.info(
                        'User "{}" ({:d}) imported {:d} proceedings' \
                            .format(uname, uid, count),
                        request)
                    return render(
                        request,
                        'szr_procbatchresult.html',
                        {'app': APP,
                         'page_title': 'Import řízení ze souboru',
                         'count': count,
                         'errors': errors})

                except:  # pragma: no cover
                    logger.error('Error reading file', request)
                    err_message = 'Chyba při načtení souboru'

    return render(
        request,
        'szr_procbatchform.html',
        {'app': APP,
         'page_title': 'Import řízení ze souboru',
         'err_message': err_message})

@require_http_methods(['GET'])
@login_required
def procexport(request):
    logger.debug('Proceedings export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    pp = Proceedings.objects.filter(uid=uid).order_by('desc', 'pk') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=szr.csv'
    writer = csvwriter(response)
    for p in pp:
        dat = [
            p.desc,
            p.court.id,
            composeref(
                p.senate,
                p.register,
                p.number,
                p.year)
        ]
        writer.writerow(dat)
    logger.info(
        'User "{}" ({:d}) exported proceedings'.format(uname, uid),
        request)
    return response

@require_http_methods(['GET'])
def courts(request):
    logger.debug('List of courts accessed', request)
    return render(
        request,
        'szr_courts.html',
        {'page_title': 'Přehled soudů',
         'rows': Court.objects.order_by('name').values('id', 'name')})
