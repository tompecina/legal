# -*- coding: utf-8 -*-
#
# sir/views.py
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

from locale import strxfrm
from csv import reader as csvreader, writer as csvwriter
from io import StringIO
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.urls import reverse
from common.utils import getbutton, Pager, logger
from common.glob import inerr
from szr.forms import EmailForm
from sir.glob import l2n, l2s
from sir.models import Vec, Insolvency
from sir.forms import InsForm
from sir.cron import p2s


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
    page_title = 'Sledování změn v insolvenčních řízeních'
    rd = request.GET.copy()
    start = int(rd['start']) if ('start' in rd) else 0
    if request.method == 'GET':
        f = EmailForm(initial=model_to_dict(get_object_or_404(User, pk=uid)))
    else:
        f = EmailForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            p = get_object_or_404(User, pk=uid)
            p.email = cd['email']
            p.save()
            return redirect('sir:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    p = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk')
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    return render(
        request,
        'sir_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sir:mainpage'), rd, BATCH),
         'total': total})


@require_http_methods(['GET', 'POST'])
@login_required
def insform(request, id=0):

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
    if request.method == 'GET':
        f = (InsForm(initial=model_to_dict(get_object_or_404( \
            Insolvency, pk=id, uid=uid))) if id else InsForm())
    elif btn == 'back':
        return redirect('sir:mainpage')
    else:
        f = InsForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Insolvency, pk=id, uid=uid)
                cd['pk'] = id
                cd['timestamp_add'] = p.timestamp_add
                cd['timestamp_update'] = p.timestamp_update
            p = Insolvency(uid_id=uid, **cd)
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
            return redirect('sir:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    return render(
        request,
        'sir_insform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(['GET', 'POST'])
@login_required
def insdel(request, id=0):

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
            'sir_insdel.html',
            {'app': APP,
             'page_title': 'Smazání řízení'})
    else:
        ins = get_object_or_404(Insolvency, pk=id, uid=uid)
        if getbutton(request) == 'yes':
            logger.info(
                'User "{}" ({:d}) deleted proceedings "{}" ({})' \
                    .format(uname, uid, ins.desc, p2s(ins)),
                request)
            ins.delete()
            return redirect('sir:insdeleted')
        return redirect('sir:mainpage')


@require_http_methods(['GET', 'POST'])
@login_required
def insdelall(request):

    logger.debug(
        'Delete all proceedings page accessed using method {}' \
            .format(request.method),
        request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'sir_insdelall.html',
            {'app': APP,
             'page_title': 'Smazání všech řízení'})
    else:
        if (getbutton(request) == 'yes') and \
           ('conf' in request.POST) and \
           (request.POST['conf'] == 'Ano'):
            Insolvency.objects.filter(uid=uid).delete()
            logger.info(
                'User "{}" ({:d}) deleted all proceedings'.format(uname, uid),
                request)
        return redirect('sir:mainpage')


@require_http_methods(['GET', 'POST'])
@login_required
def insbatchform(request):

    logger.debug(
        'Proceedings import page accessed using method {}' \
            .format(request.method),
        request)

    err_message = ''
    uid = request.user.id
    uname = request.user.username

    if request.method == 'POST':
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
                            desc = line[0].strip()
                            if not desc:
                                errors.append([i, 'Prázdný popis'])
                                continue
                            if len(desc) > 255:
                                errors.append([i, 'Příliš dlouhý popis'])
                                continue
                            try:
                                number = int(line[1])
                                assert number > 0
                            except:
                                errors.append([i, 'Chybné běžné číslo'])
                                continue
                            try:
                                year = int(line[2])
                                assert year >= 2008
                            except:
                                errors.append([i, 'Chybný ročník'])
                                continue
                            detailed = line[3].strip()
                            if detailed == 'ano':
                                detailed = True
                            elif detailed == 'ne':
                                detailed = False
                            else:
                                errors.append([i, 'Chybný údaj pro pole Vše'])
                                continue

                            if len(errors) == errlen:
                                try:
                                    Insolvency.objects.update_or_create(
                                        uid_id=uid,
                                        desc=desc,
                                        defaults={
                                            'number': number,
                                            'year': year,
                                            'detailed': detailed}
                                    )
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
                        'sir_insbatchresult.html',
                        {'app': APP,
                         'page_title': 'Import řízení ze souboru',
                         'count': count,
                         'errors': errors})

                except:  # pragma: no cover
                    logger.error('Error reading file', request)
                    err_message = 'Chyba při načtení souboru'

    return render(
        request,
        'sir_insbatchform.html',
        {'app': APP,
         'page_title': 'Import řízení ze souboru',
         'err_message': err_message})


@require_http_methods(['GET'])
@login_required
def insexport(request):

    logger.debug('Proceedings export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    ii = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=sir.csv'
    writer = csvwriter(response)
    for i in ii:
        dat = [
            i.desc,
            str(i.number),
            str(i.year),
            ('ano' if i.detailed else 'ne'),
        ]
        writer.writerow(dat)
    logger.info(
        'User "{}" ({:d}) exported proceedings'.format(uname, uid),
        request)
    return response


@require_http_methods(['GET'])
def courts(request):

    logger.debug('List of courts accessed', request)
    courts = sorted([{'short': l2s[x], 'name': l2n[x]} for x in \
        Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()], \
        key=(lambda x: strxfrm(x['name'])))
    return render(
        request,
        'sir_courts.html',
        {'page_title': 'Přehled insolvenčních soudů', 'rows': courts})
