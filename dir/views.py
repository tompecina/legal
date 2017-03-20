# -*- coding: utf-8 -*-
#
# dir/views.py
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
from datetime import date
from locale import strxfrm
from csv import reader as csvreader, writer as csvwriter
from io import StringIO
from re import compile
from common.utils import getbutton, grammar, between, Pager, logger
from common.glob import (
    inerr, GR_C, text_opts, text_opts_keys, text_opts_abbr, text_opts_ca,
    text_opts_ai, ic_regex, rc_full_regex)
from szr.forms import EmailForm
from sir.glob import l2n, l2s
from sir.models import Vec
from .glob import MAX_LENGTH
from .forms import DebtorForm
from .models import Debtor

APP = __package__

APPVERSION = apps.get_app_config(APP).version

BATCH = 50

OFIELDS = ['name', 'first_name']
OPTS = [x + '_opt' for x in OFIELDS]

@require_http_methods(['GET', 'POST'])
@login_required
def mainpage(request):

    logger.debug('Main page accessed using method ' + request.method)

    err_message = ''
    uid = request.user.id
    page_title = 'Sledování nových dlužníků v insolvenci'

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
            return redirect('dir:mainpage')
        else:
            logger.debug('Invalid form')
            err_message = inerr
    d = Debtor.objects.filter(uid=uid).order_by('desc', 'pk') \
        .values()
    total = d.count()
    if (start >= total) and (total > 0):
        start = total - 1
    rows = d[start:(start + BATCH)]
    for row in rows:
        q = QueryDict(mutable=True)
        q['role_debtor'] = q['deleted'] = 'on'
        if row['court']:
            q['court']= row['court']
        if row['name']:
            q['name']= row['name']
            q['name_opt'] = text_opts_keys[row['name_opt']]
        if row['first_name']:
            q['first_name']= row['first_name']
            q['first_name_opt'] = text_opts_keys[row['first_name_opt']]
        if row['genid']:
            q['genid']= row['genid']
        if row['taxid']:
            q['taxid']= row['taxid']
        if row['birthid']:
            q['birthid']= row['birthid']
        if row['date_birth']:
            q['date_birth']= row['date_birth']
        if row['year_birth_from']:
            q['year_birth_from']= row['year_birth_from']
        if row['year_birth_to']:
            q['year_birth_to']= row['year_birth_to']
        row['search'] = q.urlencode()
    return render(
        request,
        'dir_mainpage.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'err_message': err_message,
         'rows': rows,
         'pager': Pager(start, total, reverse('dir:mainpage'), rd, BATCH),
         'total': total})

@require_http_methods(['GET', 'POST'])
@login_required
def debtorform(request, id=0):

    logger.debug('Debtor form accessed using method ' + request.method)

    err_message = ''
    uid = request.user.id
    uname = request.user.username
    page_title = ('Úprava dlužníka' if id else 'Nový dlužník')

    btn = getbutton(request)
    courts = sorted([{'id': x, 'name': l2n[x]} for x in \
        Vec.objects.values_list('idOsobyPuvodce', flat=True).distinct()], \
        key=(lambda x: strxfrm(x['name'])))
    if request.method == 'GET':
        if id:
            d = model_to_dict(get_object_or_404(Debtor, pk=id, uid=uid))
            for o in OPTS:
                d[o] = text_opts_keys[d[o]]
            if d['birthid']:
                d['birthid'] = d['birthid'][:6] + '/' + d['birthid'][6:]
            f = DebtorForm(initial=d)
        else:
            f = DebtorForm()
    elif btn == 'back':
        return redirect('dir:mainpage')
    else:
        f = DebtorForm(request.POST)
        if f.is_valid():
            cd = f.cleaned_data
            if id:
                p = get_object_or_404(Debtor, pk=id, uid=uid)
                cd['pk'] = id
                cd['timestamp_add'] = p.timestamp_add
                cd['timestamp_update'] = p.timestamp_update
            cd['birthid'] = cd['birthid'].replace('/', '')
            for key in cd:
                if cd[key] == '':
                    cd[key] = None
            p = Debtor(uid_id=uid, **cd)
            for o in OPTS:
                p.__setattr__(o, text_opts_keys.index(cd[o]))
            p.save()
            if id:
                logger.info(
                    'User "%s" (%d) updated debtor "%s"' % (uname, uid, p.desc))
            else:
                logger.info(
                    'User "%s" (%d) added debtor "%s"' % (uname, uid, p.desc))
            return redirect('dir:mainpage')
        else:
            logger.debug('Invalid form')
            err_message = inerr
    return render(
        request,
        'dir_debtorform.html',
        {'app': APP,
         'f': f,
         'page_title': page_title,
         'courts': courts,
         'err_message': err_message})

@require_http_methods(['GET', 'POST'])
@login_required
def debtordel(request, id=0):
    logger.debug('Debtor delete page accessed using method ' + request.method)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'dir_debtordel.html',
            {'app': APP,
             'page_title': 'Smazání dlužníka'})
    else:
        debtor = get_object_or_404(Debtor, pk=id, uid=uid)
        if (getbutton(request) == 'yes'):
            logger.info(
                'User "%s" (%d) deleted debtor "%s"' % \
                (uname, uid, debtor.desc))
            debtor.delete()
            return redirect('dir:debtordeleted')
        return redirect('dir:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def debtordelall(request, id=0):
    logger.debug(
        'Delete all debtors page accessed using method ' + request.method)
    uid = request.user.id
    uname = request.user.username
    if request.method == 'GET':
        return render(
            request,
            'dir_debtordelall.html',
            {'app': APP,
             'page_title': 'Smazání všech dlužníků'})
    else:
        if (getbutton(request) == 'yes') and \
           ('conf' in request.POST) and \
           (request.POST['conf'] == 'Ano'):
            Debtor.objects.filter(uid=uid).delete()
            logger.info('User "%s" (%d) deleted all debtors' % (uname, uid))
        return redirect('dir:mainpage')

@require_http_methods(['GET', 'POST'])
@login_required
def debtorbatchform(request):

    logger.debug('Debtor import page accessed using method ' + request.method)

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
                            desc = line[0].strip()
                            court = name = first_name = genid = taxid = \
                                birthid = date_birth = year_birth_from = \
                                year_birth_to = None
                            name_opt = first_name_opt = 0
                            if not desc:
                                errors.append([i, 'Prázdný popis'])
                                continue
                            if len(desc) > 255:
                                errors.append([i, 'Příliš dlouhý popis'])
                                continue
                            for term in line[1:]:
                                if '=' not in term:
                                    errors.append([i, 'Chybný formát'])
                                    continue
                                key, value = map(
                                    (lambda x: x.strip()),
                                    term.split('=', 1))
                                if not value:
                                    continue
                                if key == 'soud':
                                    court = value
                                elif key == 'název':
                                    if ':' in value:
                                        name, name_opt = value.split(':', 1)
                                        if name_opt not in text_opts_abbr:
                                            errors.append([i, 'Chybná ' \
                                                'zkratka pro posici v poli ' \
                                                '<q>název</q>'])
                                            continue
                                        name_opt = text_opts_ai[name_opt]
                                    else:
                                        name = value
                                        name_opt = 0
                                    if len(name) > MAX_LENGTH:
                                        errors.append([i, 'Příliš dlouhé ' \
                                            'pole <q>název</q>'])
                                        continue
                                elif key == 'jméno':
                                    if ':' in value:
                                        first_name, first_name_opt = \
                                            value.split(':', 1)
                                        if first_name_opt not in text_opts_abbr:
                                            errors.append([i, 'Chybná ' \
                                                'zkratka pro posici v poli ' \
                                                '<q>jméno</q>'])
                                            continue
                                        first_name_opt = \
                                            text_opts_ai[first_name_opt]
                                    else:
                                        first_name = value
                                        first_name_opt = 0
                                    if len(first_name) > MAX_LENGTH:
                                        errors.append([i, 'Příliš dlouhé ' \
                                            'pole <q>jméno</q>'])
                                        continue
                                elif key == 'IČO':
                                    if not compile(ic_regex).match(value):
                                        errors.append([i, 'Chybná hodnota ' \
                                            'pro IČO'])
                                        continue
                                    genid = value
                                elif key == 'DIČ':
                                    if len(value) > 14:
                                        errors.append([i, 'Chybná hodnota ' \
                                            'pro DIČ'])
                                        continue
                                    taxid = value
                                elif key == 'RČ':
                                    if not compile(rc_full_regex).match(value):
                                        errors.append([i, 'Chybná hodnota ' \
                                            'pro rodné číslo'])
                                        continue
                                    birthid = value.replace('/', '')
                                elif key == 'datumNarození':
                                    try:
                                        t = value.split('.')
                                        date_birth = date(
                                            int(t[2]), int(t[1]), int(t[0]))
                                        assert date_birth.year >= 1900
                                    except:
                                        errors.append([i, 'Chybná hodnota ' \
                                            'pro datum narození'])
                                        continue
                                elif key == 'rokNarozeníOd':
                                    try:
                                        year_birth_from = int(value)
                                        assert year_birth_from >= 1900
                                    except:
                                        errors.append([i, 'Chybná hodnota ' \
                                            'pro pole <q>rokNarozeníOd</q>'])
                                        continue
                                elif key == 'rokNarozeníDo':
                                    try:
                                        year_birth_to = int(value)
                                        assert year_birth_to >= 1900
                                    except:
                                        errors.append([i, 'Chybná hodnota ' \
                                            'pro pole <q>rokNarozeníDo</q>'])
                                        continue
                                else:
                                    errors.append([i, 'Chybný parametr: "' \
                                        + key + '"'])
                                    continue
                                if year_birth_from and year_birth_to and \
                                   (year_birth_from > year_birth_to):
                                    errors.append([i, 'Chybný interval pro ' \
                                        'rok narození'])
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
                                    errors.append([i, 'Popisu "' + desc + \
                                        '" odpovídá více než jeden dlužník'])
                                    continue
                                count += 1
                    logger.info(
                        'User "%s" (%d) imported %d debtor(s)' % \
                        (uname, uid, count))
                    return render(
                        request,
                        'dir_debtorbatchresult.html',
                        {'app': APP,
                         'page_title': 'Import dlužníků ze souboru',
                         'count': count,
                         'errors': errors})

                except:  # pragma: no cover
                    logger.error('Error reading file')
                    err_message = 'Chyba při načtení souboru'
        else:
            logger.debug('Invalid form')
            err_message = inerr

    return render(
        request,
        'dir_debtorbatchform.html',
        {'app': APP,
         'page_title': 'Import dlužníků ze souboru',
         'err_message': err_message})

@require_http_methods(['GET'])
@login_required
def debtorexport(request):
    logger.debug('Debtor export page accessed')
    uid = request.user.id
    uname = request.user.username
    pp = Debtor.objects.filter(uid=uid).order_by('desc', 'pk') \
        .distinct()
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = \
        'attachment; filename=dir.csv'
    writer = csvwriter(response)
    for p in pp:
        dat = [p.desc]
        if p.court:
            dat.append('soud=' + l2s[p.court])
        if p.name:
            dat.append('název=' + p.name + text_opts_ca[p.name_opt])
        if p.first_name:
            dat.append('jméno=' + p.first_name + text_opts_ca[p.first_name_opt])
        if p.genid:
            dat.append('IČO=' + p.genid)
        if p.taxid:
            dat.append('DIČ=' + p.taxid)
        if p.birthid:
            dat.append('RČ=' + p.birthid[:6] + '/' + p.birthid[6:])
        if p.date_birth:
            dat.append('datumNarození=%02d.%02d.%d' % \
                (p.date_birth.day, p.date_birth.month, p.date_birth.year))
        if p.year_birth_from:
            dat.append('rokNarozeníOd=' + str(p.year_birth_from))
        if p.year_birth_to:
            dat.append('rokNarozeníDo=' + str(p.year_birth_to))
        writer.writerow(dat)
    logger.info('User "%s" (%d) exported debtors' % (uname, uid))
    return response
