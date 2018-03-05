# -*- coding: utf-8 -*-
#
# sur/views.py
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

from csv import reader as csvreader, writer as csvwriter
from io import StringIO

from django.shortcuts import get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.http import QueryDict
from django.urls import reverse

from legal.common.glob import INERR, GR_CHAR, TEXT_OPTS, TEXT_OPTS_KEYS, TEXT_OPTS_ABBR, TEXT_OPTS_CA, TEXT_OPTS_AI
from legal.common.utils import getbutton, grammar, between, Pager, LOGGER, render
from legal.szr.forms import EmailForm
from legal.sur.forms import PartyForm
from legal.sur.models import Party
from legal.sur.glob import MIN_LENGTH, MAX_LENGTH


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

BATCH = 50


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    err_message = ''
    uid = request.user.id
    page_title = 'Sledování účastníků řízení'

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
            return redirect('sur:mainpage')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    res = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'pk').values()
    total = res.count()
    if start >= total and total:
        start = total - 1
    rows = res[start:start + BATCH]
    for row in rows:
        row['party_opt_text'] = TEXT_OPTS[row['party_opt']][1]
        query = QueryDict(mutable=True)
        query['party'] = row['party']
        query['party_opt'] = TEXT_OPTS_KEYS[row['party_opt']]
        row['search'] = query.urlencode()
        query = QueryDict(mutable=True)
        query['text'] = '"{}"'.format(row['party'])
        row['uds_search'] = query.urlencode()
    return render(
        request,
        'sur_mainpage.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('sur:mainpage'), reqd, BATCH),
         'total': total})


@require_http_methods(('GET', 'POST'))
@login_required
def partyform(request, idx=0):

    LOGGER.debug('Party form accessed using method {}, id={}'.format(request.method, idx), request, request.POST)

    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava účastníka' if idx else 'Nový účastník'

    button = getbutton(request)
    if request.method == 'GET':
        if idx:
            dct = model_to_dict(get_object_or_404(Party, pk=idx, uid=uid))
            dct['party_opt'] = TEXT_OPTS_KEYS[dct['party_opt']]
            form = PartyForm(initial=dct)
        else:
            form = PartyForm()
    elif button == 'back':
        return redirect('sur:mainpage')
    else:
        form = PartyForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if idx:
                res = get_object_or_404(Party, pk=idx, uid=uid)
                cld['pk'] = idx
                cld['notify'] = res.notify
                cld['timestamp_add'] = res.timestamp_add
            res = Party(uid_id=uid, **cld)
            res.party_opt = TEXT_OPTS_KEYS.index(cld['party_opt'])
            res.save()
            LOGGER.info(
                'User "{}" ({:d}) {} party {}'.format(uname, uid, 'updated' if idx else 'added', res.party),
                request)
            return redirect('sur:mainpage')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    return render(
        request,
        'sur_partyform.xhtml',
        {'app': APP,
         'form': form,
         'min_chars': grammar(MIN_LENGTH, GR_CHAR),
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def partydel(request, idx=0):

    LOGGER.debug(
        'Party delete page accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    party = get_object_or_404(Party, pk=idx, uid=uid)
    if request.method == 'GET':
        return render(
            request,
            'sur_partydel.xhtml',
            {'app': APP,
             'page_title': 'Smazání účastníka',
             'desc': party.party})
    else:
        if getbutton(request) == 'yes':
            LOGGER.info('User "{}" ({:d}) deleted party "{}"'.format(uname, uid, party.party), request)
            party.delete()
            return redirect('sur:partydeleted')
        return redirect('sur:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def partydelall(request):

    LOGGER.debug('Delete all parties page accessed using method {}'.format(request.method), request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'sur_partydelall.xhtml',
            {'app': APP,
             'page_title': 'Smazání všech účastníků'})
    else:
        if getbutton(request) == 'yes' and 'conf' in request.POST and request.POST['conf'] == 'Ano':
            Party.objects.filter(uid=uid).delete()
            LOGGER.info('User "{}" ({:d}) deleted all parties'.format(uname, uid), request)
        return redirect('sur:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def partybatchform(request):

    LOGGER.debug('Party import page accessed using method {}'.format(request.method), request)

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
                            line = line[0].strip()
                            if ':' in line:
                                line, party_opt = line.split(':', 1)
                            else:
                                party_opt = '*'
                            if not between(MIN_LENGTH, len(line), MAX_LENGTH):
                                errors.append((idx, 'Chybná délka řetězce'))
                                continue
                            if party_opt not in TEXT_OPTS_ABBR:
                                errors.append((idx, 'Chybná zkratka pro posici'))
                                continue
                            if len(errors) == errlen:
                                try:
                                    Party.objects.update_or_create(
                                        uid_id=uid,
                                        party=line,
                                        defaults={'party_opt': TEXT_OPTS_AI[party_opt]}
                                    )
                                except:
                                    errors.append((idx, 'Řetězci "{}" odpovídá více než jeden účastník'.format(line)))
                                    continue
                                count += 1
                    LOGGER.info('User "{}" ({:d}) imported {} party/ies'.format(uname, uid, count), request)
                    return render(
                        request,
                        'sur_partybatchresult.xhtml',
                        {'app': APP,
                         'page_title': 'Import účastníků řízení ze souboru',
                         'count': count,
                         'errors': errors})

                except:  # pragma: no cover
                    LOGGER.error('Error reading file', request)
                    err_message = 'Chyba při načtení souboru'
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR

    return render(
        request,
        'sur_partybatchform.xhtml',
        {'app': APP,
         'page_title': 'Import účastníků řízení ze souboru',
         'err_message': err_message,
         'min_length': MIN_LENGTH,
         'max_length': MAX_LENGTH})


@require_http_methods(('GET',))
@login_required
def partyexport(request):

    LOGGER.debug('Party export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    res = Party.objects.filter(uid=uid).order_by('party', 'party_opt', 'id').distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=sur.csv'
    writer = csvwriter(response)
    for item in res:
        dat = (item.party + TEXT_OPTS_CA[item.party_opt],)
        writer.writerow(dat)
    LOGGER.info('User "{}" ({:d}) exported parties'.format(uname, uid), request)
    return response
