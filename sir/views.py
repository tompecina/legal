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

from django.shortcuts import get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.urls import reverse

from common.glob import INERR
from common.utils import getbutton, Pager, logger, render
from szr.forms import EmailForm
from sir.glob import L2N, L2S
from sir.models import Vec, Insolvency
from sir.forms import InsForm
from sir.cron import p2s


APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    logger.debug(
        'Main page accessed using method {}'.format(request.method),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    page_title = 'Sledování změn v insolvenčních řízeních'
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
            return redirect('sir:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = INERR
    res = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk')
    total = res.count()
    if start >= total and total:
        start = total - 1
    rows = res[start:start + BATCH]
    return render(
        request,
        'sir_mainpage.html',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sir:mainpage'), reqd, BATCH),
         'total': total})


@require_http_methods(('GET', 'POST'))
@login_required
def insform(request, idx=0):

    logger.debug(
        'Proceedings form accessed using method {}, id={}'
        .format(request.method, idx),
        request,
        request.POST)
    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava řízení' if idx else 'Nové řízení'
    button = getbutton(request)
    if request.method == 'GET':
        form = (InsForm(initial=model_to_dict(get_object_or_404(
            Insolvency, pk=idx, uid=uid))) if idx else InsForm())
    elif button == 'back':
        return redirect('sir:mainpage')
    else:
        form = InsForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if idx:
                res = get_object_or_404(Insolvency, pk=idx, uid=uid)
                cld['pk'] = idx
                cld['timestamp_add'] = res.timestamp_add
                cld['timestamp_update'] = res.timestamp_update
            res = Insolvency(uid_id=uid, **cld)
            res.save()
            logger.info(
                'User "{}" ({:d}) {} proceedings "{}" ({})'
                .format(
                    uname,
                    uid,
                    'updated' if idx else 'added',
                    res.desc,
                    p2s(res)),
                request)
            return redirect('sir:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = INERR
    return render(
        request,
        'sir_insform.html',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def insdel(request, idx=0):

    logger.debug(
        'Proceedings delete page accessed using method {}, id={}'
        .format(request.method, idx),
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
        ins = get_object_or_404(Insolvency, pk=idx, uid=uid)
        if getbutton(request) == 'yes':
            logger.info(
                'User "{}" ({:d}) deleted proceedings "{}" ({})'
                .format(uname, uid, ins.desc, p2s(ins)),
                request)
            ins.delete()
            return redirect('sir:insdeleted')
        return redirect('sir:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def insdelall(request):

    logger.debug(
        'Delete all proceedings page accessed using method {}'
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
        if getbutton(request) == 'yes' and 'conf' in request.POST \
           and request.POST['conf'] == 'Ano':
            Insolvency.objects.filter(uid=uid).delete()
            logger.info(
                'User "{}" ({:d}) deleted all proceedings'.format(uname, uid),
                request)
        return redirect('sir:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def insbatchform(request):

    logger.debug(
        'Proceedings import page accessed using method {}'
            .format(request.method),
        request)

    err_message = ''
    uid = request.user.id
    uname = request.user.username

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
                            desc = line[0].strip()
                            if not desc:
                                errors.append((idx, 'Prázdný popis'))
                                continue
                            if len(desc) > 255:
                                errors.append((idx, 'Příliš dlouhý popis'))
                                continue
                            try:
                                number = int(line[1])
                                assert number > 0
                            except:
                                errors.append((idx, 'Chybné běžné číslo'))
                                continue
                            try:
                                year = int(line[2])
                                assert year >= 2008
                            except:
                                errors.append((idx, 'Chybný ročník'))
                                continue
                            detailed = line[3].strip()
                            if detailed == 'ano':
                                detailed = True
                            elif detailed == 'ne':
                                detailed = False
                            else:
                                errors.append((idx, 'Chybný údaj pro pole Vše'))
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
                                        (idx,
                                         'Popisu "{}" odpovídá více než '
                                         'jedno řízení'.format(desc)))
                                    continue
                                count += 1
                    logger.info(
                        'User "{}" ({:d}) imported {:d} proceedings'
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


@require_http_methods(('GET',))
@login_required
def insexport(request):

    logger.debug('Proceedings export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    res = Insolvency.objects.filter(uid=uid).order_by('desc', 'pk') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=sir.csv'
    writer = csvwriter(response)
    for idx in res:
        dat = [
            idx.desc,
            str(idx.number),
            str(idx.year),
            'ano' if idx.detailed else 'ne',
        ]
        writer.writerow(dat)
    logger.info(
        'User "{}" ({:d}) exported proceedings'.format(uname, uid),
        request)
    return response


@require_http_methods(('GET',))
def courts(request):

    logger.debug('List of courts accessed', request)
    rows = sorted([{'short': L2S[x], 'name': L2N[x]} for x in
        Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()],
        key=lambda x: strxfrm(x['name']))
    return render(
        request,
        'sir_courts.html',
        {'page_title': 'Přehled insolvenčních soudů', 'rows': rows})
