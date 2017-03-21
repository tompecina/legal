# -*- coding: utf-8 -*-
#
# sur/views.py
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
from django.http import QueryDict
from django.urls import reverse
from csv import reader as csvreader, writer as csvwriter
from io import StringIO
from common.utils import getbutton, grammar, between, Pager, logger
from common.glob import (
    inerr, GR_C, text_opts, text_opts_keys, text_opts_abbr, text_opts_ca,
    text_opts_ai)
from szr.forms import EmailForm
from .forms import PartyForm
from .models import Party
from .glob import MIN_LENGTH, MAX_LENGTH

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):

    logger.debug(
        'Main page accessed using method ' + request.method,
        request)

    err_message = ''
    uid = request.user.id
    page_title = 'Sledování účastníků řízení'

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
            return redirect('sur:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    p = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'pk') \
        .values()
    total = p.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = p[start:(start + BATCH)]
    for row in rows:
        row['party_opt_text'] = text_opts[row['party_opt']][1]
        q = QueryDict(mutable=True)
        q['party']= row['party']
        q['party_opt'] = text_opts_keys[row['party_opt']]
        row['search'] = q.urlencode()
    return render(
        request,
        'sur_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sur:mainpage'), rd, BATCH),
         'total': total})

@require_http_methods(['GET', 'POST'])
@login_required
def partyform(request, id=0):

    logger.debug(
        'Party form accessed using method ' + request.method,
        request)

    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = ('Úprava účastníka' if id else 'Nový účastník')

    btn = getbutton(request)
    if request.method == 'GET':
        if id:
            d = model_to_dict(get_object_or_404(Party, pk=id, uid=uid))
            d['party_opt'] = text_opts_keys[d['party_opt']]
            f = PartyForm(initial=d)
        else:
            f = PartyForm()
    elif btn == 'back':
        return redirect('sur:mainpage')
    else:
        f = PartyForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Party, pk=id, uid=uid)
                cd['pk'] = id
                cd['timestamp_add'] = p.timestamp_add
                cd['timestamp_update'] = p.timestamp_update
            p = Party(uid_id=uid, **cd)
            p.party_opt = text_opts_keys.index(cd['party_opt'])
            if id:
                logger.info(
                    'User "%s" (%d) updated party "%s"' % (uname, uid, p.party),
                    request)
            else:
                logger.info(
                    'User "%s" (%d) added party "%s"' % (uname, uid, p.party),
                    request)
            p.save()
            return redirect('sur:mainpage')
        else:
            logger.debug('Invalid form', request)
            err_message = inerr
    return render(
        request,
        'sur_partyform.html',
        {'app': APP,
         'f': f,
         'min_chars': grammar(MIN_LENGTH, GR_C),
         'page_title': page_title,
         'err_message': err_message})

@require_http_methods(['GET', 'POST'])
@login_required
def partydel(request, id=0):
    logger.debug(
        'Party delete page accessed using method ' + request.method,
        request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'sur_partydel.html',
            {'app': APP,
             'page_title': 'Smazání účastníka'})
    else:
        party = get_object_or_404(Party, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            logger.info(
                'User "%s" (%d) deleted party "%s"' % (uname, uid, party.party),
                request)
            party.delete()
            return redirect('sur:partydeleted')
        return redirect('sur:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def partydelall(request):
    logger.debug(
        'Delete all parties page accessed using method ' + request.method,
        request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'sur_partydelall.html',
            {'app': APP,
             'page_title': 'Smazání všech účastníků'})
    else:
        if (getbutton(request) == 'yes') and \
           ('conf' in request.POST) and \
           (request.POST['conf'] == 'Ano'):
            Party.objects.filter(uid=uid).delete()
            logger.info(
                'User "%s" (%d) deleted all parties' % (uname, uid),
                request)
        return redirect('sur:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def partybatchform(request):

    logger.debug(
        'Party import page accessed using method ' + request.method,
        request)

    err_message = ''
    uid = request.user.id
    uname = request.user.username

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
                            line = line[0].strip()
                            if ':' in line:
                               line, party_opt = line.split(':', 1)
                            else:
                                party_opt = '*'
                            if not between(MIN_LENGTH, len(line), MAX_LENGTH):
                                errors.append([i, 'Chybná délka řetězce'])
                                continue
                            if party_opt not in text_opts_abbr:
                                errors.append([i, 'Chybná zkratka pro posici'])
                                continue
                            if len(errors) == errlen:
                                try:
                                    Party.objects.update_or_create(
                                        uid_id=uid,
                                        party=line,
                                        defaults={'party_opt': \
                                            text_opts_ai[party_opt]}
                                    )
                                except:
                                    errors.append([i, 'Řetězci "' + line + \
                                        '" odpovídá více než jeden účastník'])
                                    continue
                                count += 1
                    logger.info(
                        'User "%s" (%d) imported %d party/ies' % \
                        (uname, uid, count),
                        request)
                    return render(
                        request,
                        'sur_partybatchresult.html',
                        {'app': APP,
                         'page_title': 'Import účastníků řízení ze souboru',
                         'count': count,
                         'errors': errors})

                except:  # pragma: no cover
                    logger.error('Error reading file', request)
                    err_message = 'Chyba při načtení souboru'
        else:
            logger.debug('Invalid form', request)
            err_message = inerr

    return render(
        request,
        'sur_partybatchform.html',
        {'app': APP,
         'page_title': 'Import účastníků řízení ze souboru',
         'err_message': err_message,
         'min_length': MIN_LENGTH,
         'max_length': MAX_LENGTH})

@require_http_methods(['GET'])
@login_required
def partyexport(request):
    logger.debug('Party export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    pp = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'id') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=sur.csv'
    writer = csvwriter(response)
    for p in pp:
        dat = [p.party + text_opts_ca[p.party_opt]]
        writer.writerow(dat)
    logger.info(
        'User "%s" (%d) exported parties' % (uname, uid),
        request)
    return response
