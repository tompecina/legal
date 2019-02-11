# -*- coding: utf-8 -*-
#
# dir/views.py
#
# Copyright (C) 2011-19 Tomáš Pecina <tomas@pecina.cz>
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
from re import compile

from django.shortcuts import get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.apps import apps
from django.http import QueryDict
from django.urls import reverse

from legal.common.glob import (
    INERR, TEXT_OPTS_KEYS, TEXT_OPTS_ABBR, TEXT_OPTS_CA, TEXT_OPTS_AI, IC_RE_STR, RC_FULL_RE_STR)
from legal.common.utils import getbutton, Pager, LOGGER, render
from legal.szr.forms import EmailForm
from legal.sir.glob import L2S
from legal.dir.glob import MAX_LENGTH
from legal.dir.forms import DebtorForm
from legal.dir.models import Debtor


APP = __package__.rpartition('.')[2]

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

OFIELDS = ('name', 'first_name')
OPTS = [key + '_opt' for key in OFIELDS]


@require_http_methods(('GET', 'POST'))
@login_required
def mainpage(request):

    LOGGER.debug('Main page accessed using method {}'.format(request.method), request, request.POST)

    err_message = ''
    uid = request.user.id
    page_title = 'Sledování nových dlužníků v insolvenci'

    rdt = request.GET.copy()
    start = int(rdt['start']) if 'start' in rdt else 0
    if request.method == 'GET':
        form = EmailForm(initial=model_to_dict(get_object_or_404(User, pk=uid)))
    else:
        form = EmailForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            user = get_object_or_404(User, pk=uid)
            user.email = cld['email']
            user.save()
            return redirect('dir:mainpage')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    debtors = Debtor.objects.filter(uid=uid).order_by('desc', 'pk').values()
    total = debtors.count()
    if start >= total and total:
        start = total - 1
    rows = debtors[start:(start + BATCH)]
    for row in rows:
        query = QueryDict(mutable=True)
        query['role_debtor'] = query['deleted'] = 'on'
        for key in ('court', 'genid', 'taxid', 'birthid', 'date_birth', 'year_birth_from', 'year_birth_to'):
            if row[key]:
                query[key] = row[key]
        for key in OFIELDS:
            if row[key]:
                query[key] = row[key]
                key_opt = '{}_opt'.format(key)
                query[key_opt] = TEXT_OPTS_KEYS[row[key_opt]]
        row['search'] = query.urlencode()
    return render(
        request,
        'dir_mainpage.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('dir:mainpage'), rdt, BATCH),
         'total': total})


@require_http_methods(('GET', 'POST'))
@login_required
def debtorform(request, idx=0):

    LOGGER.debug(
        'Debtor form accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)

    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = 'Úprava dlužníka' if idx else 'Nový dlužník'

    button = getbutton(request)
    if request.method == 'GET':
        if idx:
            debtor = model_to_dict(get_object_or_404(Debtor, pk=idx, uid=uid))
            for opt in OPTS:
                debtor[opt] = TEXT_OPTS_KEYS[debtor[opt]]
            if debtor['birthid']:
                debtor['birthid'] = '{}/{}'.format(debtor['birthid'][:6], debtor['birthid'][6:])
            form = DebtorForm(initial=debtor)
        else:
            form = DebtorForm()
    elif button == 'back':
        return redirect('dir:mainpage')
    else:
        form = DebtorForm(request.POST)
        if form.is_valid():
            cld = form.cleaned_data
            if idx:
                debtor = get_object_or_404(Debtor, pk=idx, uid=uid)
                cld['pk'] = idx
                cld['notify'] = debtor.notify
                cld['timestamp_add'] = debtor.timestamp_add
            cld['birthid'] = cld['birthid'].replace('/', '')
            for key in cld:
                if cld[key] == '':
                    cld[key] = None
            debtor = Debtor(uid_id=uid, **cld)
            for opt in OPTS:
                debtor.__setattr__(opt, TEXT_OPTS_KEYS.index(cld[opt]))
            debtor.save()
            LOGGER.info(
                'User "{}" ({:d}) {} debtor {}'.format(uname, uid, 'updated' if idx else 'added', debtor.desc),
                request)
            return redirect('dir:mainpage')
        else:
            LOGGER.debug('Invalid form', request)
            err_message = INERR
    return render(
        request,
        'dir_debtorform.xhtml',
        {'app': APP,
         'form': form,
         'page_title': page_title,
         'err_message': err_message})


@require_http_methods(('GET', 'POST'))
@login_required
def debtordel(request, idx=0):

    LOGGER.debug(
        'Debtor delete page accessed using method {}, id={}'.format(request.method, idx),
        request,
        request.POST)
    uid = request.user.id
    uname = request.user.username
    debtor = get_object_or_404(Debtor, pk=idx, uid=uid)
    if request.method == 'GET':
        return render(
            request,
            'dir_debtordel.xhtml',
            {'app': APP,
             'page_title': 'Smazání dlužníka',
             'desc': debtor.desc})
    else:
        if getbutton(request) == 'yes':
            LOGGER.info('User "{}" ({:d}) deleted debtor "{}"'.format(uname, uid, debtor.desc), request)
            debtor.delete()
            return redirect('dir:debtordeleted')
        return redirect('dir:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def debtordelall(request):

    LOGGER.debug('Delete all debtors page accessed using method {}'.format(request.method), request)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'dir_debtordelall.xhtml',
            {'app': APP,
             'page_title': 'Smazání všech dlužníků'})
    else:
        if getbutton(request) == 'yes' and 'conf' in request.POST and request.POST['conf'] == 'Ano':
            Debtor.objects.filter(uid=uid).delete()
            LOGGER.info('User "{}" ({:d}) deleted all debtors'.format(uname, uid), request)
        return redirect('dir:mainpage')


@require_http_methods(('GET', 'POST'))
@login_required
def debtorbatchform(request):

    LOGGER.debug('Debtor import page accessed using method {}'.format(request.method), request)

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
                            court = name = first_name = genid = taxid = birthid = date_birth = year_birth_from \
                                = year_birth_to = None
                            name_opt = first_name_opt = 0
                            if not desc:
                                errors.append((idx, 'Prázdný popis'))
                                continue
                            if len(desc) > 255:
                                errors.append((idx, 'Příliš dlouhý popis'))
                                continue
                            for term in line[1:]:
                                if '=' not in term:
                                    errors.append((idx, 'Chybný formát'))
                                    continue
                                key, val = map(
                                    lambda x: x.strip(),
                                    term.split('=', 1))
                                if not val:
                                    continue
                                if key == 'soud':
                                    court = val
                                elif key == 'název':
                                    if ':' in val:
                                        name, name_opt = val.split(':', 1)
                                        if name_opt not in TEXT_OPTS_ABBR:
                                            errors.append((idx, 'Chybná zkratka pro posici v poli <q>název</q>'))
                                            continue
                                        name_opt = TEXT_OPTS_AI[name_opt]
                                    else:
                                        name = val
                                        name_opt = 0
                                    if len(name) > MAX_LENGTH:
                                        errors.append((idx, 'Příliš dlouhé pole <q>název</q>'))
                                        continue
                                elif key == 'jméno':
                                    if ':' in val:
                                        first_name, first_name_opt = val.split(':', 1)
                                        if first_name_opt not in TEXT_OPTS_ABBR:
                                            errors.append((idx, 'Chybná zkratka pro posici v poli <q>jméno</q>'))
                                            continue
                                        first_name_opt = TEXT_OPTS_AI[first_name_opt]
                                    else:
                                        first_name = val
                                        first_name_opt = 0
                                    if len(first_name) > MAX_LENGTH:
                                        errors.append((idx, 'Příliš dlouhé pole <q>jméno</q>'))
                                        continue
                                elif key == 'IČO':
                                    if not compile(IC_RE_STR).match(val):
                                        errors.append((idx, 'Chybná hodnota pro IČO'))
                                        continue
                                    genid = val
                                elif key == 'DIČ':
                                    if len(val) > 14:
                                        errors.append((idx, 'Chybná hodnota pro DIČ'))
                                        continue
                                    taxid = val
                                elif key == 'RČ':
                                    if not compile(RC_FULL_RE_STR).match(val):
                                        errors.append((idx, 'Chybná hodnota pro rodné číslo'))
                                        continue
                                    birthid = val.replace('/', '')
                                elif key == 'datumNarození':
                                    try:
                                        date_birth = date(*map(int, val.split('.')[2::-1]))
                                        assert date_birth.year >= 1900
                                    except:
                                        errors.append((idx, 'Chybná hodnota pro datum narození'))
                                        continue
                                elif key == 'rokNarozeníOd':
                                    try:
                                        year_birth_from = int(val)
                                        assert year_birth_from >= 1900
                                    except:
                                        errors.append((idx, 'Chybná hodnota pro pole <q>rokNarozeníOd</q>'))
                                        continue
                                elif key == 'rokNarozeníDo':
                                    try:
                                        year_birth_to = int(val)
                                        assert year_birth_to >= 1900
                                    except:
                                        errors.append((idx, 'Chybná hodnota pro pole <q>rokNarozeníDo</q>'))
                                        continue
                                else:
                                    errors.append((idx, 'Chybný parametr: "{}"'.format(key)))
                                    continue
                                if year_birth_from and year_birth_to and year_birth_from > year_birth_to:
                                    errors.append((idx, 'Chybný interval pro rok narození'))
                                    continue

                            if len(errors) == errlen:
                                try:
                                    Debtor.objects.update_or_create(
                                        uid_id=uid,
                                        desc=desc,
                                        defaults={
                                            'court': court,
                                            'name': name,
                                            'name_opt': name_opt,
                                            'first_name': first_name,
                                            'first_name_opt': first_name_opt,
                                            'genid': genid,
                                            'taxid': taxid,
                                            'birthid': birthid,
                                            'date_birth': date_birth,
                                            'year_birth_from': year_birth_from,
                                            'year_birth_to': year_birth_to}
                                    )
                                except:
                                    errors.append((idx, 'Popisu "{}" odpovídá více než jeden dlužník'.format(desc)))
                                    continue
                                count += 1
                    LOGGER.info('User "{}" ({:d}) imported {:d} debtor(s)'.format(uname, uid, count), request)
                    return render(
                        request,
                        'dir_debtorbatchresult.xhtml',
                        {'app': APP,
                         'page_title': 'Import dlužníků ze souboru',
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
        'dir_debtorbatchform.xhtml',
        {'app': APP,
         'page_title': 'Import dlužníků ze souboru',
         'err_message': err_message})


@require_http_methods(('GET',))
@login_required
def debtorexport(request):

    LOGGER.debug('Debtor export page accessed', request)
    uid = request.user.id
    uname = request.user.username
    debtors = Debtor.objects.filter(uid=uid).order_by('desc', 'pk').distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename=dir.csv'
    writer = csvwriter(response)
    for debtor in debtors:
        dat = [debtor.desc]
        if debtor.court:
            dat.append('soud={}'.format(L2S[debtor.court]))
        if debtor.name:
            dat.append('název={}'.format(
                debtor.name + TEXT_OPTS_CA[debtor.name_opt]))
        if debtor.first_name:
            dat.append('jméno={}'.format(
                debtor.first_name + TEXT_OPTS_CA[debtor.first_name_opt]))
        if debtor.genid:
            dat.append('IČO={}'.format(debtor.genid))
        if debtor.taxid:
            dat.append('DIČ={}'.format(debtor.taxid))
        if debtor.birthid:
            dat.append('RČ={}/{}'.format(
                debtor.birthid[:6],
                debtor.birthid[6:]))
        if debtor.date_birth:
            dat.append('datumNarození={0.day:02d}.{0.month:02d}.{0.year:d}'.format(debtor.date_birth))
        if debtor.year_birth_from:
            dat.append('rokNarozeníOd={:d}'.format(debtor.year_birth_from))
        if debtor.year_birth_to:
            dat.append('rokNarozeníDo={:d}'.format(debtor.year_birth_to))
        writer.writerow(dat)
    LOGGER.info('User "{}" ({:d}) exported debtors'.format(uname, uid), request)
    return response
